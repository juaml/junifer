"""Provide tests for base."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import pytest

from junifer.storage.base import BaseFeatureStorage


def test_BaseFeatureStorage_abstractness() -> None:
    """Test BaseFeatureStorage is abstract base class."""
    with pytest.raises(TypeError, match=r"abstract"):
        BaseFeatureStorage(uri="/tmp", storage_types=["matrix"])


def test_BaseFeatureStorage() -> None:
    """Test proper subclassing of BaseFeatureStorage."""
    # Create concrete class
    class MyFeatureStorage(BaseFeatureStorage):
        """Implement concrete class."""

        def __init__(self, uri, single_output=False):
            storage_types = ["matrix"]
            super().__init__(
                uri=uri,
                storage_types=storage_types,
                single_output=single_output,
            )

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

    # Check single_output is False
    st = MyFeatureStorage(uri="/tmp")
    assert st.single_output is False
    # Check single_output is True
    st = MyFeatureStorage(uri="/tmp", single_output=True)
    assert st.single_output is True

    # Check validate with valid argument
    st.validate(input_=["matrix"])
    # Check validate with invalid argument
    with pytest.raises(ValueError):
        st.validate(input_=["table"])

    with pytest.raises(NotImplementedError):
        st.list_features()

    with pytest.raises(NotImplementedError):
        st.read_df(None)

    with pytest.raises(NotImplementedError):
        st.store_metadata(None)

    with pytest.raises(NotImplementedError):
        st.collect()

    with pytest.raises(NotImplementedError):
        st.store(kind="matrix")

    with pytest.raises(NotImplementedError):
        st.store(kind="timeseries")

    with pytest.raises(NotImplementedError):
        st.store(kind="table")

    with pytest.raises(ValueError):
        st.store(kind="lego")

    assert st.uri == "/tmp"
