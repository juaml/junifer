"""Provide tests for lagged functional connectivity using parcels."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

from junifer.datareader import DefaultDataReader
from junifer.markers.functional_connectivity import (
    FunctionalConnectivityLaggedParcels,
)
from junifer.storage import HDF5FeatureStorage
from junifer.testing.datagrabbers import PartlyCloudyTestingDataGrabber


def test_FunctionalConnectivityLaggedParcels(
    tmp_path: Path,
) -> None:
    """Test FunctionalConnectivityLaggedParcels.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with PartlyCloudyTestingDataGrabber() as dg:
        # Get element data
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        # Setup marker
        marker = FunctionalConnectivityLaggedParcels(
            parcellation="TianxS1x3TxMNInonlinear2009cAsym",
            max_lag=10,
        )
        # Check correct outputs
        assert "matrix" == marker.get_output_type(
            input_type="BOLD", output_feature="functional_connectivity"
        )
        assert "matrix" == marker.get_output_type(
            input_type="BOLD", output_feature="lag"
        )

        # Fit-transform the data and check
        lagged_fc = marker.fit_transform(element_data)

        for feature in ("functional_connectivity", "lag"):
            lagged_fc_bold = lagged_fc["BOLD"][feature]

            assert "data" in lagged_fc_bold
            assert "row_names" in lagged_fc_bold
            assert "col_names" in lagged_fc_bold
            assert lagged_fc_bold["data"].shape == (16, 16)
            assert len(set(lagged_fc_bold["row_names"])) == 16
            assert len(set(lagged_fc_bold["col_names"])) == 16

        # Store
        storage = HDF5FeatureStorage(
            uri=tmp_path / "test_lagged_fc_parcels.hdf5",
        )
        marker.fit_transform(input=element_data, storage=storage)
        features = storage.list_features()
        assert all(
            x["name"]
            in (
                (
                    "BOLD_FunctionalConnectivityLaggedParcels_"
                    "functional_connectivity"
                ),
                "BOLD_FunctionalConnectivityLaggedParcels_lag",
            )
            for x in features.values()
        )
