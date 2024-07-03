"""Provide tests for temporal signal-to-noise ratio using parcellation."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

from junifer.datareader import DefaultDataReader
from junifer.markers.temporal_snr import TemporalSNRParcels
from junifer.storage import HDF5FeatureStorage
from junifer.testing.datagrabbers import PartlyCloudyTestingDataGrabber


def test_TemporalSNRParcels_computation() -> None:
    """Test TemporalSNRParcels fit-transform."""
    with PartlyCloudyTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        marker = TemporalSNRParcels(
            parcellation="TianxS1x3TxMNInonlinear2009cAsym"
        )
        # Check correct output
        assert "vector" == marker.get_output_type(
            input_type="BOLD", output_feature="tsnr"
        )

        # Fit-transform the data
        tsnr_parcels = marker.fit_transform(element_data)
        tsnr_parcels_bold = tsnr_parcels["BOLD"]["tsnr"]

        assert "data" in tsnr_parcels_bold
        assert "col_names" in tsnr_parcels_bold
        assert tsnr_parcels_bold["data"].shape == (1, 16)
        assert len(set(tsnr_parcels_bold["col_names"])) == 16


def test_TemporalSNRParcels_storage(tmp_path: Path) -> None:
    """Test TemporalSNRParcels store.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with PartlyCloudyTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        marker = TemporalSNRParcels(
            parcellation="TianxS1x3TxMNInonlinear2009cAsym"
        )
        # Store
        storage = HDF5FeatureStorage(tmp_path / "test_tsnr_parcels.hdf5")
        marker.fit_transform(input=element_data, storage=storage)
        features = storage.list_features()
        assert any(
            x["name"] == "BOLD_TemporalSNRParcels_tsnr"
            for x in features.values()
        )
