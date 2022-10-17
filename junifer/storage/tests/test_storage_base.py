"""Provide tests for base."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import pytest

from junifer.storage.base import BaseFeatureStorage


def test_BaseFeatureStorage_abstractness() -> None:
    """Test BaseFeatureStorage is abstract base class."""
    with pytest.raises(TypeError, match=r"abstract"):
        BaseFeatureStorage(uri="/tmp")  # type: ignore


def test_BaseFeatureStorage() -> None:
    """Test BaseFeatureStorage."""
    # Create concrete class
    class MyFeatureStorage(BaseFeatureStorage):
        def __init__(self, uri, single_output=False):
            super().__init__(uri, single_output=single_output)

        def validate_input(self, input):
            super().validate_input(input)

        def list_features(self):
            super().list_features()

        def read_df(self, feature_name=None, feature_md5=None):
            super().read_df(
                feature_name=feature_name,
                feature_md5=feature_md5,
            )

        def store_metadata(self, metadata):
            super().store_metadata(metadata)

        def collect(self):
            return super().collect()

    st = MyFeatureStorage(uri="/tmp")
    assert st.single_output is False

    st = MyFeatureStorage(uri="/tmp", single_output=True)
    assert st.single_output is True

    with pytest.raises(NotImplementedError):
        st.validate_input(None)

    with pytest.raises(NotImplementedError):
        st.list_features()

    with pytest.raises(NotImplementedError):
        st.read_df(None)

    with pytest.raises(NotImplementedError):
        st.store_metadata(None)

    with pytest.raises(NotImplementedError):
        st.collect()

    assert st.uri == "/tmp"
