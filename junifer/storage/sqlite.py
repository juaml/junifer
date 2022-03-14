# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
import pandas as pd
from pandas.core.base import NoNewAttributesMixin
from pandas.io.sql import pandasSQL_builder
from sqlalchemy import create_engine, inspect

from .base import PandasFeatureStoreage, element_to_index, meta_hash
from ..utils.logging import warn


class SQLiteFeatureStorage(PandasFeatureStoreage):
    """
    SQLite feature storage.
    """

    def __init__(self, uri, upsert='update'):
        """Initialise an SQLite feature storage

        Parameters
        ----------
        uri : str
            The connection URI.
            Easy options:
                'sqlite://' for an in memory sqlite database
                'sqlite:///<path_to_file>' to save in a file

            Check https://docs.sqlalchemy.org/en/14/core/engines.html for more
            options
        upsert : str
            Upsert mode. Options are 'ignore' and 'update' (default). If
            'ignore', the existing elements are ignored. If update, the
            existing elements are updated.

        """
        if upsert not in ['update', 'ignore']:
            raise ValueError('upsert must be either "update" or "ignore"')
        super().__init__(uri)
        self._engine = create_engine(uri, echo=False)
        self._upsert = upsert

    def store_metadata(self, meta):
        t_meta = meta.copy()
        t_meta.update(self.get_meta())
        meta_md5 = meta_hash(t_meta)
        if meta_md5 not in inspect(self._engine).get_table_names():
            meta_df = self._meta_row(t_meta, meta_md5)
            self._save_upsert(meta_df, 'meta')
        return f'meta_{meta_md5}'

    def store_matrix2d(
            self, data, meta, col_names=None, rows_col_name=None):
        # Same as store_2d, but order is important
        raise NotImplementedError('store_matrix2d not implemented')

    def store_table(self, data, meta, columns=None, rows_col_name=None):
        self.store_2d(data, meta, columns, rows_col_name)

    def store_2d(self, data, meta, columns=None, rows_col_name=None):
        n_rows = len(data)
        idx = element_to_index(
            meta, n_rows=n_rows, rows_col_name=rows_col_name)
        data_df = pd.DataFrame(data, columns=columns, index=idx)
        self.store_df(data_df, meta)

    def store_df(self, df, meta):
        table_name = self.store_metadata(meta)
        self._save_upsert(df, table_name)

    def store_timeseries(self, data, meta):
        raise NotImplementedError('store_timeseries not implemented')

    def _save_upsert(self, df, name, if_exist='append'):
        """ Implemention of UPSERT functionality.

        Parameters
        ----------
        df : pandas.DataFrame
            DataFrame to save
        name : str
            Name of the table to save
        if_exist : str
            If the table exists, the behavior is controlled by this parameter.
            Options are 'append' (default) and 'fail'. If 'fail' and th table
            exists, it will raise an error. If 'append', the data will be
            appended to the existing table (following the upsert mode).

        Raises
        ______
        ValueError
            If the table exists and if_exist is 'fail'
        """
        index_col = df.index.names
        with self._engine.begin() as con:
            if if_exist == 'replace':
                # Case 1: replace all the existing elements
                df.to_sql(name, con=con, if_exists='replace')
            elif not inspect(self._engine).has_table(name):
                # Case 2: new table, so no big issue
                df.to_sql(name, con=con, if_exists='append')
            else:
                # Case 3: existing table, so we need to check if the index
                # is present or not.
                if if_exist == 'fail':
                    raise ValueError(f"Table ({name}) already exists")

                # Step 1: split incoming data into existing and new data
                pk_indb = _get_existing_pk(
                    con, table_name=name, index_col=index_col)
                existing, new = _split_incoming_data(df, pk_indb, index_col)

                # Step 2: upsert existing data
                pandas_sql = pandasSQL_builder(con)
                pandas_sql.meta.reflect(bind=con, only=[name])
                table = pandas_sql.get_table(name)
                update_stmts = NoNewAttributesMixin
                if len(existing) > 0 and len(new) > 0:
                    warn(
                        f"Some rows (n={len(existing)}) are already present "
                        "in the database. The storage is configured to "
                        f"{self._upsert} the existing elements. The new rows "
                        f"(n={len(new)}) will be appended. This warning "
                        "is shown because normally all of the elements should "
                        "be updated")
                if self._upsert == 'update':
                    update_stmts = _generate_update_statements(
                        table, index_col, existing)
                    for stmt in update_stmts:
                        con.execute(stmt)

                # Step 3: insert new data
                new.to_sql(name, con=con, if_exists='append')


def _get_existing_pk(con, table_name, index_col):
    pk_cols = ','.join(index_col)
    query = f'SELECT {pk_cols} FROM {table_name};'
    pk_indb = pd.read_sql(query, con=con)
    return pk_indb


def _split_incoming_data(df, pk_indb, index_col):
    incoming_pk = df.reset_index()[index_col]
    exists_mask = (
        incoming_pk[index_col]
        .apply(tuple, axis=1)
        .isin(pk_indb[index_col].apply(tuple, axis=1))
    )
    existing, new = df.loc[exists_mask.values], df.loc[~exists_mask.values]
    return existing, new


def _generate_update_statements(table, index_col, rows_to_update):
    from sqlalchemy import and_

    new_records = rows_to_update.to_dict(orient="records")
    pk_indb = rows_to_update.reset_index()[index_col]
    pk_cols = [table.c[key] for key in index_col]

    stmts = []
    for i, (_, keys) in enumerate(pk_indb.iterrows()):
        stmt = (
            table.update()
            .where(and_(col == keys[j]
                        for j, col in enumerate(pk_cols)))  # type: ignore
            .values(new_records[i])
        )
        stmts.append(stmt)
    return stmts
