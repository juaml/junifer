"""Provide tests for temporal signal-to-noise ratio using maps."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

import pytest

from junifer.datagrabber import DataType
from junifer.datareader import DefaultDataReader
from junifer.markers import TemporalSNRMaps
from junifer.storage import HDF5FeatureStorage
from junifer.testing.datagrabbers import ADHDTestingDataGrabber


pytestmark = pytest.mark.external


def test_TemporalSNRMaps_computation() -> None:
    """Test TemporalSNRMaps fit-transform."""
    with ADHDTestingDataGrabber() as dg:
        element = dg["sub-01"]
        element_data = DefaultDataReader().fit_transform(element)
        marker = TemporalSNRMaps(maps="Smith_rsn_10")
        # Check correct output
        assert "vector" == marker.storage_type(
            input_type=DataType.BOLD, output_feature="tsnr"
        )
        # Fit-transform the data
        bold_img = element_data["BOLD"]["data"]
        tsnr_parcels = marker.fit_transform(element_data)
        # The input is not changed
        assert element_data["BOLD"]["data"] is bold_img
        tsnr_parcels_bold = tsnr_parcels["BOLD"]["tsnr"]

        assert "data" in tsnr_parcels_bold
        assert "col_names" in tsnr_parcels_bold
        assert tsnr_parcels_bold["data"].shape == (1, 10)
        assert len(set(tsnr_parcels_bold["col_names"])) == 10


def test_TemporalSNRMaps_storage(tmp_path: Path) -> None:
    """Test TemporalSNRMaps store.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with ADHDTestingDataGrabber() as dg:
        element = dg["sub-01"]
        element_data = DefaultDataReader().fit_transform(element)
        marker = TemporalSNRMaps(maps="Smith_rsn_10")
        # Store
        storage = HDF5FeatureStorage(uri=tmp_path / "test_tsnr_maps.hdf5")
        marker.fit_transform(input=element_data, storage=storage)
        features = storage.list_features()
        assert any(
            x["name"] == "BOLD_TemporalSNRMaps_tsnr" for x in features.values()
        )
