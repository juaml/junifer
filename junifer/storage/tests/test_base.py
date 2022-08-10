"""Provide tests for base."""

import pytest

from junifer.storage.base import BaseFeatureStorage
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

    assert st.uri == "/tmp"
