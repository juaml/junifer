"""Provide tests for lagged functional connectivity using spheres."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

import pytest

from junifer.datareader import DefaultDataReader
from junifer.markers.functional_connectivity import (
    FunctionalConnectivityLaggedSpheres,
)
from junifer.storage import HDF5FeatureStorage
from junifer.testing.datagrabbers import SPMAuditoryTestingDataGrabber


def test_FunctionalConnectivitySpheres(
    tmp_path: Path,
) -> None:
    """Test FunctionalConnectivityLaggedSpheres.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with SPMAuditoryTestingDataGrabber() as dg:
        # Get element data
        element_data = DefaultDataReader().fit_transform(dg["sub001"])
        # Setup marker
        marker = FunctionalConnectivityLaggedSpheres(
            coords="DMNBuckner",
            radius=5.0,
            max_lag=10,
        )
        # Check correct outputs
        assert "matrix" == marker.get_output_type(
            input_type="BOLD", output_feature="functional_connectivity"
        )
        assert "matrix" == marker.get_output_type(
            input_type="BOLD", output_feature="lag"
        )

        # Fit-transform the data
        lagged_fc = marker.fit_transform(element_data)

        for feature in ("functional_connectivity", "lag"):
            lagged_fc_bold = lagged_fc["BOLD"][feature]

            assert "data" in lagged_fc_bold
            assert "row_names" in lagged_fc_bold
            assert "col_names" in lagged_fc_bold
            assert lagged_fc_bold["data"].shape == (6, 6)
            assert len(set(lagged_fc_bold["row_names"])) == 6
            assert len(set(lagged_fc_bold["col_names"])) == 6

        # Store
        storage = HDF5FeatureStorage(
            uri=tmp_path / "test_lagged_fc_spheres.hdf5",
        )
        marker.fit_transform(input=element_data, storage=storage)
        features = storage.list_features()
        assert all(
            x["name"]
            in (
                (
                    "BOLD_FunctionalConnectivityLaggedSpheres_"
                    "functional_connectivity"
                ),
                "BOLD_FunctionalConnectivityLaggedSpheres_lag",
            )
            for x in features.values()
        )


def test_FunctionalConnectivityLaggedSpheres_error() -> None:
    """Test FunctionalConnectivityLaggedSpheres errors."""
    with pytest.raises(ValueError, match="radius should be > 0"):
        FunctionalConnectivityLaggedSpheres(
            coords="DMNBuckner", radius=-0.1, max_lag=10
        )
