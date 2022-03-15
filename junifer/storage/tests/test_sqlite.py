import pandas as pd
from pandas.testing import assert_frame_equal
import tempfile
from sqlalchemy import create_engine
import pytest

from junifer.storage.sqlite import SQLiteFeatureStorage
from junifer.storage.base import process_meta


df1 = pd.DataFrame({
    'pk1': [1, 2, 3, 4, 5],
    'pk2': ['a', 'b', 'c', 'd', 'e'],
    'col1': [11, 22, 33, 44, 55],
    'col2': [111, 222, 333, 444, 555]
}).set_index(['pk1', 'pk2'])

df2 = pd.DataFrame({
    'pk1': [2, 5, 6],
    'pk2': ['b', 'e', 'f'],
    'col1': [2222, 5555, 66],
    'col2': [22222, 55555, 666]
}).set_index(['pk1', 'pk2'])

df_update = pd.DataFrame({
    'pk1': [1, 2, 3, 4, 5, 6],
    'pk2': ['a', 'b', 'c', 'd', 'e', 'f'],
    'col1': [11, 2222, 33, 44, 5555, 66],
    'col2': [111, 22222, 333, 444, 55555, 666]
}).set_index(['pk1', 'pk2'])

df_ignore = pd.DataFrame({
    'pk1': [1, 2, 3, 4, 5, 6],
    'pk2': ['a', 'b', 'c', 'd', 'e', 'f'],
    'col1': [11, 22, 33, 44, 55, 66],
    'col2': [111, 222, 333, 444, 555, 666]
}).set_index(['pk1', 'pk2'])


def _read_sql(table_name, uri, index_col):
    engine = create_engine(uri, echo=False)
    df = pd.read_sql(table_name, con=engine, index_col=index_col)
    return df


def test_upsert_replace():
    """Test store_df (if_exist=replace)"""
    with tempfile.TemporaryDirectory() as _tmpdir:
        uri = f'sqlite:///{_tmpdir}/test.db'
        storage = SQLiteFeatureStorage(uri=uri, upsert='ignore')
        meta = {'element': 'test', 'version': '0.0.1'}

        # Save to SQL
        storage.store_df(df1, meta)

        # Test the internals
        table_name = storage.store_metadata(meta)

        c_df1 = _read_sql(table_name, uri=uri, index_col=['pk1', 'pk2'])
        assert_frame_equal(df1, c_df1)

        storage._save_upsert(df2, table_name, if_exist='replace')

        c_df2 = _read_sql(table_name, uri=uri, index_col=['pk1', 'pk2'])
        assert_frame_equal(df2, c_df2)


def test_upsert_ignore():
    """Test store_df (upsert=ignore)"""
    with tempfile.TemporaryDirectory() as _tmpdir:
        uri = f'sqlite:///{_tmpdir}/test.db'
        with pytest.raises(ValueError):
            SQLiteFeatureStorage(uri=uri, upsert='wrong')

        storage = SQLiteFeatureStorage(uri=uri, upsert='ignore')
        meta = {'element': 'test', 'version': '0.0.1'}

        # Save to SQL
        storage.store_df(df1, meta)

        # Test the internals
        table_name = storage.store_metadata(meta)

        c_df1 = _read_sql(table_name, uri=uri, index_col=['pk1', 'pk2'])
        assert_frame_equal(df1, c_df1)

        storage.store_df(df2, meta)

        c_dfignore = _read_sql(table_name, uri=uri, index_col=['pk1', 'pk2'])
        assert_frame_equal(c_dfignore, df_ignore)

        with pytest.raises(ValueError, match=r"already exists"):
            storage._save_upsert(df2, table_name, if_exist='fail')


def test_upsert_update():
    """Test store_df (upsert=delete)"""
    meta = {'element': 'test', 'version': '0.0.1'}
    with tempfile.TemporaryDirectory() as _tmpdir:
        uri = f'sqlite:///{_tmpdir}/test.db'
        storage = SQLiteFeatureStorage(uri=uri)

        # Save to SQL
        storage.store_df(df1, meta)

        # Test the internals
        table_name = storage.store_metadata(meta)

        c_df1 = _read_sql(table_name, uri=uri, index_col=['pk1', 'pk2'])
        assert_frame_equal(df1, c_df1)

        storage.store_df(df2, meta)

        c_dfupdate = _read_sql(table_name, uri=uri, index_col=['pk1', 'pk2'])
        assert_frame_equal(c_dfupdate, df_update)


def test_store_read_df():
    """Test store_df"""
    with tempfile.TemporaryDirectory() as _tmpdir:
        uri = f'sqlite:///{_tmpdir}/test.db'
        storage = SQLiteFeatureStorage(uri=uri, upsert='ignore')
        meta = {
            'element': 'test', 'version': '0.0.1',
            'marker': {'name': 'fcname'}}

        to_store = df1[['col1', 'col2']]

        # Save to SQL
        with pytest.raises(ValueError, match=r"index of the dataframe"):
            storage.store_df(to_store, meta)

        _, _, idx = process_meta(  # type: ignore
            meta, return_idx=True, n_rows=len(to_store))
        to_store = to_store.set_index(idx)

        storage.store_df(to_store, meta)

        # Test the internals
        table_name = storage.store_metadata(meta)

        features = storage.list_features()
        assert len(features) == 1
        assert table_name.replace('meta_', '') in features

        with pytest.raises(ValueError, match='not found'):
            storage.read_df('wrong_md5')

        with pytest.raises(ValueError, match='least one'):
            storage.read_df()

        with pytest.raises(ValueError, match='Only one'):
            storage.read_df('wrong_md5', 'wrong_name')

        feature_md5 = list(features.keys())[0]
        assert 'fcname' == features[feature_md5]['name']
        read_df1 = storage.read_df(feature_md5=feature_md5)
        read_df2 = storage.read_df(feature_name='fcname')
        assert_frame_equal(read_df1, read_df2)
        assert_frame_equal(read_df1, to_store.reset_index())


def test_store_table():
    """Test store_table"""
    meta = {'element': 'test', 'version': '0.0.1', 'marker': {'name': 'fc'}}
    with tempfile.TemporaryDirectory() as _tmpdir:
        uri = f'sqlite:///{_tmpdir}/test.db'
        storage = SQLiteFeatureStorage(uri=uri)
        data = [
            [1, 10],
            [2, 20],
            [3, 30],
            [4, 40],
            [5, 50],
        ]
        _, _, idx = process_meta(  # type: ignore
            meta, return_idx=True, n_rows=5, rows_col_name='scan')
        df1 = pd.DataFrame(data, columns=['f1', 'f2'], index=idx)

        storage.store_table(
            data, meta, columns=['f1', 'f2'], rows_col_name='scan')

        table_name = storage.store_metadata(meta)
        c_df1 = _read_sql(table_name, uri=uri, index_col=['element', 'scan'])
        assert_frame_equal(df1, c_df1)

        data2 = [
            [1, 10],
            [2, 20],
            [3, 300],
            [4, 40],
            [5, 50],
            [6, 600]
        ]

        _, _, idx = process_meta(  # type: ignore
            meta, return_idx=True, n_rows=6, rows_col_name='scan')
        df2 = pd.DataFrame(data2, columns=['f1', 'f2'], index=idx)

        with pytest.warns(RuntimeWarning, match=r"Some rows"):
            storage.store_table(
                data2, meta, columns=['f1', 'f2'], rows_col_name='scan')

        c_df2 = _read_sql(table_name, uri=uri, index_col=['element', 'scan'])
        assert_frame_equal(df2, c_df2)
