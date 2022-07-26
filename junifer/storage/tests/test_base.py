"""Provide tests for base."""

import pytest

from junifer.storage.base import (process_meta, element_to_index,
                                  BaseFeatureStorage,
                                  element_to_prefix)


def test_process_meta_hash():
    """Test metadata hash."""
    meta = None
    with pytest.raises(ValueError, match=r"Meta must be a dict"):
        process_meta(meta)

    meta = {'element': 'foo', 'A': 1, 'B': [2, 3, 4, 5, 6]}
    hash1, _ = process_meta(meta)

    meta = {'element': 'foo', 'B': [2, 3, 4, 5, 6], 'A': 1}
    hash2, _ = process_meta(meta)
    assert hash1 == hash2

    meta = {'element': 'foo', 'A': 1, 'B': [2, 3, 1, 5, 6]}
    hash3, _ = process_meta(meta)
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

    hash4, _ = process_meta(meta1)
    hash5, _ = process_meta(meta2)
    assert hash4 == hash5


def test_process_meta_element():
    """Test metadata element."""
    meta = {}
    with pytest.raises(ValueError, match=r"_element_keys"):
        process_meta(meta)

    meta = {'element': 'foo', 'A': 1, 'B': [2, 3, 4, 5, 6]}
    _, new_meta = process_meta(meta)
    assert '_element_keys' in new_meta
    assert new_meta['_element_keys'] == ['element']
    assert 'A' in new_meta
    assert 'B' in new_meta

    meta = {
        'element': {'subject': 'foo', 'session': 'bar'},
        'B': [2, 3, 4, 5, 6], 'A': 1}
    _, new_meta = process_meta(meta)
    assert '_element_keys' in new_meta
    assert new_meta['_element_keys'] == ['subject', 'session']
    assert 'A' in new_meta
    assert 'B' in new_meta


def test_process_meta_index():
    """Test metadata element to index."""
    meta = {'noelement': 'foo'}
    with pytest.raises(ValueError, match=r'meta must contain the key'):
        element_to_index(meta)

    meta = {'element': 'foo', 'A': 1, 'B': [2, 3, 4, 5, 6]}
    index = element_to_index(meta)
    assert index.names == ['element', 'idx']
    assert index.levels[0].name == 'element'
    assert index.levels[0].values[0] == 'foo'
    assert all(x == 'foo' for x in index.levels[0].values)
    assert index.levels[0].values.shape == (1,)
    assert index.levels[1].name == 'idx'
    assert all(x == i for i, x in enumerate(index.levels[1].values))
    assert index.levels[1].values.shape == (1,)

    index = element_to_index(meta, n_rows=10)
    assert index.names == ['element', 'idx']
    assert index.levels[0].name == 'element'
    assert all(x == 'foo' for x in index.levels[0].values)
    assert index.levels[0].values.shape == (1,)

    assert index.levels[1].name == 'idx'
    assert all(x == i for i, x in enumerate(index.levels[1].values))
    assert index.levels[1].values.shape == (10,)

    index = element_to_index(meta, n_rows=1, rows_col_name='scan')
    assert index.names == ['element', 'scan']
    assert index.levels[0].name == 'element'
    assert index.levels[0].values[0] == 'foo'
    assert all(x == 'foo' for x in index.levels[0].values)
    assert index.levels[0].values.shape == (1,)
    assert index.levels[1].name == 'scan'
    assert all(x == i for i, x in enumerate(index.levels[1].values))
    assert index.levels[1].values.shape == (1,)

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

    assert index.levels[2].name == 'idx'
    assert all(x == i for i, x in enumerate(index.levels[2].values))
    assert index.levels[2].values.shape == (10,)


def test_BaseFeatureStorage():
    """Test BaseFeatureStorage."""
    with pytest.raises(TypeError, match=r"abstract"):
        BaseFeatureStorage(uri='/tmp')  # type: ignore

    class MyFeatureStorage(BaseFeatureStorage):
        def __init__(self, uri, single_output=False):
            super().__init__(uri, single_output=single_output)

        def validate(self, input):
            super().validate(input)

        def list_features(self):
            super().list_features()

        def read_df(self, feature_name=None, feature_md5=None):
            super().read_df(
                feature_name=feature_name, feature_md5=feature_md5)

        def store_metadata(self, metadata):
            super().store_metadata(metadata)

        def store_matrix2d(self, matrix, meta):
            super().store_matrix2d(matrix, meta)

        def store_table(self, table, meta):
            super().store_table(table, meta)

        def store_df(self, df, meta):
            super().store_df(df, meta)

        def store_timeseries(self, timeseries, meta):
            super().store_timeseries(timeseries, meta)

        def collect(self):
            return super().collect()

    st = MyFeatureStorage(uri='/tmp')
    assert st.single_output is False

    st = MyFeatureStorage(uri='/tmp', single_output=True)
    assert st.single_output is True

    with pytest.raises(NotImplementedError):
        st.validate(None)

    with pytest.raises(NotImplementedError):
        st.list_features()

    with pytest.raises(NotImplementedError):
        st.read_df(None)

    with pytest.raises(NotImplementedError):
        st.store_metadata(None)

    with pytest.raises(NotImplementedError):
        st.store_matrix2d(None, None)

    with pytest.raises(NotImplementedError):
        st.store_table(None, None)

    with pytest.raises(NotImplementedError):
        st.store_df(None, None)

    with pytest.raises(NotImplementedError):
        st.store_timeseries(None, None)

    with pytest.raises(NotImplementedError):
        st.collect()

    assert st.uri == '/tmp'


def test_element_to_prefix():
    """Test converting element to prefix (for file naming)."""

    element = 'sub-01'
    prefix = element_to_prefix(element)
    assert prefix == 'element_sub-01_'

    element = 1
    prefix = element_to_prefix(element)
    assert prefix == 'element_1_'

    element = {'subject': 'sub-01'}
    prefix = element_to_prefix(element)
    assert prefix == 'element_sub-01_'

    element = {'subject': 1}
    prefix = element_to_prefix(element)
    assert prefix == 'element_1_'

    element = {'subject': 'sub-01', 'session': 'ses-02'}
    prefix = element_to_prefix(element)
    assert prefix == 'element_sub-01_ses-02_'

    element = {'subject': 1, 'session': 2}
    prefix = element_to_prefix(element)
    assert prefix == 'element_1_2_'

    element = ('sub-01', 'ses-02')
    prefix = element_to_prefix(element)
    assert prefix == 'element_sub-01_ses-02_'

    element = (1, 2)
    prefix = element_to_prefix(element)
    assert prefix == 'element_1_2_'
