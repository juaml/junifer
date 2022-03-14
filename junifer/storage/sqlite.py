# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
import pandas as pd
from pandas.core.base import NoNewAttributesMixin
from pandas.io.sql import pandasSQL_builder
from sqlalchemy import create_engine, inspect
import hashlib
import json
from .base import PandasFeatureStoreage, element_to_index, meta_hash


class SQLiteFeatureStorage(PandasFeatureStoreage):
    """
    SQLite feature storage.
    """

    def __init__(self, uri):
        super().__init__(uri)
        self._engine = create_engine(uri, echo=False)

    def store_metadata(self, meta):
        t_meta = meta.copy()
        t_meta.update(self.get_meta())
        meta_md5 = meta_hash(t_meta)
        if meta_md5 not in inspect(self._engine).get_table_names():
            meta_df = self._meta_row(t_meta, meta_md5)
            self._save_upsert(meta_df, 'meta')
        return meta_md5

    def store_matrix2d(self, data, col_names=None, row_names=None, meta=None):
        # Same as store_2d, but order is important
        raise NotImplementedError('store_matrix2d not implemented')

    def store_2d(self, data, meta, columns=None, row_names=None):
        idx = element_to_index(
            meta, n_rows=data.shape[0], row_names=row_names)
        data_df = pd.DataFrame(data, columns=columns, index=idx)
        self.store_df(data_df, meta)

    def store_df(self, df, meta):
        table_name = self.store_metadata(meta)
        self._save_upsert(df, table_name)

    def store_timeseries(self, data):
        raise NotImplementedError('store_timeseries not implemented')

    def _save_upsert(self, df, name, upsert='ignore', if_exist='append'):
        if upsert not in ['delete', 'ignore']:
            raise ValueError('upsert must be either "delete" or "ignore"')

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

                # Step 1: split incoming data into existing and new data
                pk_indb = _get_existing_pk(
                    con, table_name=name, index_col=index_col)
                existing, new = _split_incoming_data(df, pk_indb, index_col)

                # Step 2: upsert existing data
                pandas_sql = pandasSQL_builder(con)
                pandas_sql.meta.reflect(only=[name])
                table = pandas_sql.get_table(name)
                update_stmts = NoNewAttributesMixin
                if upsert == 'delete':
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
