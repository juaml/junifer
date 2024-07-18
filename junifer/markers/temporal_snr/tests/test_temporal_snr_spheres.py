"""Provide tests for temporal signal-to-noise spheres."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

import pytest

from junifer.datareader import DefaultDataReader
from junifer.markers.temporal_snr import TemporalSNRSpheres
from junifer.storage import HDF5FeatureStorage
from junifer.testing.datagrabbers import SPMAuditoryTestingDataGrabber


def test_TemporalSNRSpheres_computation() -> None:
    """Test TemporalSNRSpheres fit-transform."""
    with SPMAuditoryTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub001"])
        marker = TemporalSNRSpheres(coords="DMNBuckner", radius=5.0)
        # Check correct output
        assert "vector" == marker.get_output_type(
            input_type="BOLD", output_feature="tsnr"
        )

        # Fit-transform the data
        tsnr_spheres = marker.fit_transform(element_data)
        tsnr_spheres_bold = tsnr_spheres["BOLD"]["tsnr"]

        assert "data" in tsnr_spheres_bold
        assert "col_names" in tsnr_spheres_bold
        assert tsnr_spheres_bold["data"].shape == (1, 6)
        assert len(set(tsnr_spheres_bold["col_names"])) == 6


def test_TemporalSNRSpheres_storage(tmp_path: Path) -> None:
    """Test TemporalSNRSpheres store.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with SPMAuditoryTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub001"])
        marker = TemporalSNRSpheres(coords="DMNBuckner", radius=5.0)
        # Store
        storage = HDF5FeatureStorage(tmp_path / "test_tsnr_spheres.hdf5")
        marker.fit_transform(input=element_data, storage=storage)
        features = storage.list_features()
        assert any(
            x["name"] == "BOLD_TemporalSNRSpheres_tsnr"
            for x in features.values()
        )


def test_TemporalSNRSpheres_error() -> None:
    """Test TemporalSNRSpheres errors."""
    with pytest.raises(ValueError, match="radius should be > 0"):
        TemporalSNRSpheres(coords="DMNBuckner", radius=-0.1)
