# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
from pathlib import Path
import pandas as pd
from pandas.core.base import NoNewAttributesMixin
from pandas.io.sql import pandasSQL_builder
from sqlalchemy import create_engine, inspect
import tqdm 

from ..api.decorators import register_storage
from .base import (PandasFeatureStoreage, process_meta, element_to_prefix,
                   element_to_index)
from ..utils.logging import warn, logger


@register_storage
class SQLiteFeatureStorage(PandasFeatureStoreage):
    """
    SQLite feature storage.
    """

    def __init__(self, uri, single_output=False, upsert='update'):
        """Initialise an SQLite feature storage

        Parameters
        ----------
        uri : str or Path (must be a file)
            The Path to the file to be used.
        single_output : bool
            If False (default), will create one file per element. The name
            of the file will be prefixed with the respective element.
            If True, will create only one file, the specified in the URI and
            store all the elements in the same file. This behaviour is only
            suitable for non-parallel executions. SQLite does not support
            concurrency.
        upsert : str
            Upsert mode. Options are 'ignore' and 'update' (default). If
            'ignore', the existing elements are ignored. If update, the
            existing elements are updated.

        """
        if upsert not in ['update', 'ignore']:
            raise ValueError('upsert must be either "update" or "ignore"')
        if not isinstance(uri, Path):
            uri = Path(uri)
        if not uri.parent.exists():
            logger.info(f'Output directory ({uri.parent.as_posix()}) '
                        'does not exist, creating')
            uri.parent.mkdir(parents=True, exist_ok=True)
        super().__init__(uri, single_output=single_output)
        self._upsert = upsert
        self._valid_inputs = ['table', 'timeseries']

    def validate(self, input):
        if not isinstance(input, list):
            input = [input]
        return all(x in self._valid_inputs for x in input)

    def get_engine(self, meta=None):
        if meta is None:
            meta = {}
        element = meta.get('element', None)
        if self.single_output is False and element is None:
            raise ValueError(
                'element must be specified when single_output is False')
        prefix = ''
        if self.single_output is False:
            prefix = element_to_prefix(element)

        uri = f'sqlite:///{self.uri.parent}/{prefix}{self.uri.name}'
        return create_engine(uri, echo=False)

    def list_features(self, return_df=False):
        meta_df = pd.read_sql(
            'meta', con=self.get_engine(), index_col='meta_md5')
        out = meta_df
        if return_df is False:
            out = meta_df.to_dict(orient='index')
        return out

    def read_df(self, feature_name=None, feature_md5=None):
        """Read features from the storage.

        Parameters
        ----------
        feature_name : str
            Name of the feature to read. At least one of feature_name or
            feature_md5 must be specified.
        feature_md5 : str
            MD5 of the feature to read. At least one of feature_name or
            feature_md5 must be specified.

        Returns
        -------
        pandas.DataFrame
            The features.
        """
        engine = self.get_engine()
        if feature_md5 is not None and feature_name is not None:
            raise ValueError('Only one of feature_name or feature_md5 can be '
                             'specified')
        elif feature_md5 is None and feature_name is None:
            raise ValueError('At least one of feature_name or feature_md5 '
                             'must be specified')
        elif feature_md5 is not None:
            table_name = f'meta_{feature_md5}'
        else:
            meta_df = pd.read_sql(
                'meta', con=engine, index_col='meta_md5')
            t_df = meta_df.query(f"name == '{feature_name}'")
            if len(t_df) == 0:
                raise ValueError(f'Feature {feature_name} not found')
            elif len(t_df) > 1:
                raise ValueError(
                    f'More than one feature with name {feature_name} found',
                    'This file is invalid. You can bypass this issue by '
                    'specifying a feature_md5')
            table_name = f'meta_{t_df.index[0]}'
        df = pd.read_sql(table_name, con=engine)
        # Read the index:
        query = ("SELECT ii.name FROM sqlite_master AS m, "
                 "pragma_index_list(m.name) AS il, "
                 "pragma_index_info(il.name) AS ii "
                 f"WHERE tbl_name='{table_name}' "
                 "ORDER BY cid;")
        index_names = pd.read_sql(query, con=engine).values.squeeze().tolist()
        df = df.set_index(index_names)
        return df

    def store_metadata(self, meta):
        t_meta = meta.copy()
        t_meta.update(self.get_meta())
        meta_md5, t_meta_row = process_meta(t_meta)
        engine = self.get_engine(t_meta)
        if meta_md5 not in inspect(engine).get_table_names():
            meta_df = self._meta_row(t_meta_row, meta_md5)
            self._save_upsert(meta_df, 'meta', engine)
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
        # TODO: Test this function
        # Check that the index generated by meta matches the one in
        # the dataframe.
        idx = element_to_index(meta)
        # Given the meta, we might not know if there is an extra column added
        # when storing a timeseries or 2d elements. We need to check if the
        # extra element is only one.
        extra = [x for x in df.index.names if x not in idx.names]
        if len(extra) > 1:
            raise ValueError(
                'The index of the dataframe has extra items that are not '
                'in the index generated from the meta data.')
        elif len(extra) == 1:
            # The df has one extra index item, this should be the new name
            # of the missing element in the index
            idx = element_to_index(meta, rows_col_name=extra[0])

        if any(x not in df.index.names for x in idx.names):
            raise ValueError(
                'The index of the dataframe is missing index items that are '
                'generated from the meta data.')

        table_name = self.store_metadata(meta)
        # Save
        engine = self.get_engine(meta)
        self._save_upsert(df, table_name, engine)

    def store_timeseries(self, data, meta):
        raise NotImplementedError('store_timeseries not implemented')

    def collect(self):
        if self.single_output is True:
            raise ValueError('collect is not implemented for single output')
        logger.info(
            f'Collecting data from {self.uri.parent}/*{self.uri.name}')

        out_storage = SQLiteFeatureStorage(
            uri=self.uri, single_output=True, upsert='ignore')

        files = self.uri.parent.glob(f'*{self.uri.name}')
        for elem in tqdm.tqdm(files, desc='file'):
            logger.debug(f'Reading from {elem.as_posix()}')
            in_storage = SQLiteFeatureStorage(uri=elem, single_output=True)
            in_engine = in_storage.get_engine()
            # Open "meta" table
            t_meta_df = pd.read_sql(
                'meta', con=in_engine, index_col='meta_md5')
            out_storage._save_upsert(t_meta_df, 'meta')
            for meta_md5 in tqdm.tqdm(t_meta_df.index, desc='feature'):
                logger.debug(f'Collecting feature {meta_md5}')
                # TODO: Fix this, needs that read_feature sets the index
                # properly
                table_name = f'meta_{meta_md5}'
                t_df = in_storage.read_df(feature_md5=meta_md5)
                out_storage._save_upsert(t_df, table_name, if_exist='nocheck')

    def _save_upsert(self, df, name, engine=None, if_exist='append'):
        """ Implementation of UPSERT functionality.

        Parameters
        ----------
        df : pandas.DataFrame
            DataFrame to save
        name : str
            Name of the table to save
        if_exist : str
            If the table exists, the behavior is controlled by this parameter.
            Options are 'append' (default) and 'fail'. If 'fail' and the table
            exists, it will raise an error. If 'append', the data will be
            appended to the existing table (following the upsert mode).

        Raises
        ______
        ValueError
            If the table exists and if_exist is 'fail'
        """
        index_col = df.index.names
        if engine is None:
            engine = self.get_engine()
        with engine.begin() as con:
            if if_exist == 'replace':
                # Case 1: replace all the existing elements
                df.to_sql(name, con=con, if_exists='replace')
            elif not inspect(engine).has_table(name):
                # Case 2: new table, so no big issue
                df.to_sql(name, con=con, if_exists='append')
            elif if_exist == 'nocheck':
                # Case 3: existing table, but we will not check for
                # existing
                df.to_sql(name, con=con, if_exists='append')
            else:
                # Case 4: existing table, so we need to check if the index
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
    pk_cols = ', '.join(index_col)
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
