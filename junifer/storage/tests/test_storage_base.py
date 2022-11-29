"""Provide tests for base."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import pytest

from junifer.storage.base import BaseFeatureStorage


def test_BaseFeatureStorage_abstractness() -> None:
    """Test BaseFeatureStorage is abstract base class."""
    with pytest.raises(TypeError, match=r"abstract"):
        BaseFeatureStorage(uri="/tm", storage_types=["matrix"])  # type: ignore


def test_BaseFeatureStorage() -> None:
    """Test proper subclassing of BaseFeatureStorage."""
    # Create concrete class
    class MyFeatureStorage(BaseFeatureStorage):
        """Implement concrete class."""

        def __init__(self, uri, single_output=False):
            storage_types = ["matrix", "table", "timeseries"]
            super().__init__(
                uri=uri,
                storage_types=storage_types,
                single_output=single_output,
            )

        def get_valid_inputs(self):
            return ["matrix", "table", "timeseries"]

        def list_features(self):
            super().list_features()

        def read_df(self, feature_name=None, feature_md5=None):
            super().read_df(
                feature_name=feature_name,
                feature_md5=feature_md5,
            )

        def store_metadata(self, meta_md5, meta, element):
            super().store_metadata(meta_md5, meta, element)

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
        st.validate(input_=["duck"])

    with pytest.raises(NotImplementedError):
        st.list_features()

    with pytest.raises(NotImplementedError):
        st.read_df(None)

    element = {"subject": "test"}
    dependencies = ["numpy"]
    meta = {
        "element": element,
        "dependencies": dependencies,
        "marker": {"name": "fc"},
        "type": "BOLD",
    }

    with pytest.raises(NotImplementedError):
        st.store(kind="matrix", meta=meta)

    with pytest.raises(NotImplementedError):
        st.store_metadata("md5", meta=meta, element={})

    with pytest.raises(NotImplementedError):
        st.collect()

    with pytest.raises(NotImplementedError):
        st.store(kind="timeseries", meta=meta)

    with pytest.raises(NotImplementedError):
        st.store(kind="table", meta=meta)

    with pytest.raises(ValueError):
        st.store(kind="lego", meta=meta)

    assert st.uri == "/tmp"
