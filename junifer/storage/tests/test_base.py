import pytest

from junifer.storage.base import (meta_hash, element_to_index,
                                  BaseFeatureStorage)


def test_meta_hash():
    """Test meta_hash"""

    meta = {}
    hash = meta_hash(meta)

    assert hash == '99914b932bd37a50b983c5e7c90ae93b'  # empty dict

    meta = None
    with pytest.raises(ValueError, match=r"Meta must be a dict"):
        meta_hash(meta)

    meta = {'element': 'foo', 'A': 1, 'B': [2, 3, 4, 5, 6]}
    hash1 = meta_hash(meta)

    meta = {'element': 'foo', 'B': [2, 3, 4, 5, 6], 'A': 1}
    hash2 = meta_hash(meta)

    assert hash1 == hash2

    meta = {'element': 'foo', 'A': 1, 'B': [2, 3, 1, 5, 6]}
    hash3 = meta_hash(meta)
    assert hash1 != hash3

    meta1 = {
        'element': 'foo',
        'B': {
            'B2': [2, 3, 4, 5, 6], 
            'B1': [9.22, 3.14, 1.41, 5.67, 6.28],
            'B3': (1, 'car'),
        },
        'A': 1}

    meta2 = {
        'A': 1,
        'B': {
            'B3': (1, 'car'),
            'B1': [9.22, 3.14, 1.41, 5.67, 6.28],
            'B2': [2, 3, 4, 5, 6],
        },
        'element': 'foo'
    }

    hash4 = meta_hash(meta1)
    hash5 = meta_hash(meta2)
    assert hash4 == hash5


def test_element_to_index():
    """Test element_to_index"""

    meta = {'element': 'foo', 'A': 1, 'B': [2, 3, 4, 5, 6]}
    index = element_to_index(meta)
    assert index.names == ['element']
    assert index.levels[0].name == 'element'
    assert index.levels[0].values[0] == 'foo'

    index = element_to_index(meta, n_rows=10)
    assert index.names == ['element', 'index']
    assert index.levels[0].name == 'element'
    assert all(x == 'foo' for x in index.levels[0].values)
    assert index.levels[0].values.shape == (1,)

    assert index.levels[1].name == 'index'
    assert all(x == i for i, x in enumerate(index.levels[1].values))
    assert index.levels[1].values.shape == (10,)

    index = element_to_index(meta, n_rows=1, rows_col_name='scan')
    assert index.names == ['element']
    assert index.levels[0].name == 'element'
    assert all(x == 'foo' for x in index.levels[0].values)
    assert index.levels[0].values.shape == (1,)

    index = element_to_index(meta, n_rows=7, rows_col_name='scan')
    assert index.names == ['element', 'scan']
    assert index.levels[0].name == 'element'
    assert all(x == 'foo' for x in index.levels[0].values)
    assert index.levels[0].values.shape == (1,)

    assert index.levels[1].name == 'scan'
    assert all(x == i for i, x in enumerate(index.levels[1].values))
    assert index.levels[1].values.shape == (7,)

    meta = {
        'element': {'subject': 'sub-01', 'session': 'ses-01'},
        'A': 1, 'B': [2, 3, 4, 5, 6]}
    index = element_to_index(meta, n_rows=10)

    assert index.levels[0].name == 'subject'
    assert all(x == 'sub-01' for x in index.levels[0].values)
    assert index.levels[0].values.shape == (1,)

    assert index.levels[1].name == 'session'
    assert all(x == 'ses-01' for x in index.levels[1].values)
    assert index.levels[1].values.shape == (1,)

    assert index.levels[2].name == 'index'
    assert all(x == i for i, x in enumerate(index.levels[2].values))
    assert index.levels[2].values.shape == (10,)


def test_BaseFeatureStorage():
    """Test BaseFeatureStorage"""
    with pytest.raises(TypeError, match=r"abstract"):
        BaseFeatureStorage(uri='/tmp')  # type: ignore

    class MyFeatureStorage(BaseFeatureStorage):
        def store_metadata(self, metadata):
            super().store_metadata(metadata)

        def store_matrix2d(self, matrix):
            super().store_matrix2d(matrix)

        def store_table(self, table):
            super().store_table(table)

        def store_df(self, df):
            super().store_df(df)

        def store_timeseries(self, timeseries):
            super().store_timeseries(timeseries)

    st = MyFeatureStorage(uri='/tmp')
    with pytest.raises(NotImplementedError):
        st.store_metadata(None)

    with pytest.raises(NotImplementedError):
        st.store_matrix2d(None)

    with pytest.raises(NotImplementedError):
        st.store_table(None)

    with pytest.raises(NotImplementedError):
        st.store_df(None)

    with pytest.raises(NotImplementedError):
        st.store_timeseries(None)

    assert st.uri == '/tmp'
