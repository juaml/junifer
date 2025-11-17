"""Provide tests for base."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from collections.abc import Sequence
from pathlib import Path
from typing import ClassVar

import pytest

from junifer.storage import BaseFeatureStorage, StorageType


def test_BaseFeatureStorage_abstractness() -> None:
    """Test BaseFeatureStorage is abstract base class."""
    with pytest.raises(TypeError, match=r"abstract"):
        BaseFeatureStorage(uri=Path("."))


def test_BaseFeatureStorage() -> None:
    """Test proper subclassing of BaseFeatureStorage."""

    # Create concrete class
    class MyFeatureStorage(BaseFeatureStorage):
        """Implement concrete class."""

        _STORAGE_TYPES: ClassVar[Sequence[StorageType]] = [
            StorageType.Matrix,
            StorageType.Vector,
            StorageType.Timeseries,
            StorageType.Timeseries2D,
        ]

        def list_features(self):
            super().list_features()

        def read(self, feature_name=None, feature_md5=None):
            super().read(
                feature_name=feature_name,
                feature_md5=feature_md5,
            )

        def read_df(self, feature_name=None, feature_md5=None):
            super().read_df(
                feature_name=feature_name,
                feature_md5=feature_md5,
            )

        def store_metadata(self, meta_md5, element, meta):
            super().store_metadata(meta_md5, meta, element)

        def collect(self):
            super().collect()

    # Check single_output is False
    st = MyFeatureStorage(uri=Path("."), single_output=False)
    assert st.single_output is False
    # Check single_output is True
    st = MyFeatureStorage(uri=Path("."), single_output=True)
    assert st.single_output is True

    # Check validate with valid argument
    st.validate(input_=["matrix"])
    # Check validate with invalid argument
    with pytest.raises(ValueError):
        st.validate(input_=["duck"])

    with pytest.raises(NotImplementedError):
        st.list_features()

    with pytest.raises(NotImplementedError):
        st.read(None)

    with pytest.raises(NotImplementedError):
        st.read_df(None)

    meta = {
        "element": {"subject": "test"},
        "dependencies": ["numpy"],
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
        st.store(kind="timeseries_2d", meta=meta)

    with pytest.raises(NotImplementedError):
        st.store(kind="vector", meta=meta)

    with pytest.raises(ValueError):
        st.store(kind="lego", meta=meta)

    assert str(st.uri) == "."
