"""Provide tests for edge-centric functional connectivity using maps."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

import pytest

from junifer.datagrabber import PatternDataladDataGrabber
from junifer.datareader import DefaultDataReader
from junifer.markers import EdgeCentricFCMaps
from junifer.storage import HDF5FeatureStorage


@pytest.mark.parametrize(
    "conn_method_params",
    [
        {"empirical": False},
        {"empirical": True},
    ],
)
def test_EdgeCentricFCMaps(
    tmp_path: Path,
    maps_datagrabber: PatternDataladDataGrabber,
    conn_method_params: dict[str, bool],
) -> None:
    """Test EdgeCentricFCMaps.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    maps_datagrabber : PatternDataladDataGrabber
        The testing PatternDataladDataGrabber, as fixture.
    conn_method_params : dict
        The parametrized parameters to connectivity measure method.

    """
    with maps_datagrabber as dg:
        element = dg[("sub-01", "sub-001", "rest", "1")]
        element_data = DefaultDataReader().fit_transform(element)
        # Setup marker
        marker = EdgeCentricFCMaps(
            maps="Smith_rsn_10",
            conn_method="correlation",
            conn_method_params=conn_method_params,
        )
        # Check correct output
        assert "matrix" == marker.get_output_type(
            input_type="BOLD", output_feature="functional_connectivity"
        )

        # Fit-transform the data
        edge_fc = marker.fit_transform(element_data)
        edge_fc_bold = edge_fc["BOLD"]["functional_connectivity"]

        # For 10 ROIs we should get (10 * (10 -1) / 2) edges in the ETS
        n_edges = int(10 * (10 - 1) / 2)
        assert "data" in edge_fc_bold
        assert "row_names" in edge_fc_bold
        assert "col_names" in edge_fc_bold
        assert edge_fc_bold["data"].shape == (n_edges, n_edges)
        assert len(set(edge_fc_bold["row_names"])) == n_edges
        assert len(set(edge_fc_bold["col_names"])) == n_edges

        # Store
        storage = HDF5FeatureStorage(uri=tmp_path / "test_edge_fc_maps.hdf5")
        marker.fit_transform(input=element_data, storage=storage)
        features = storage.list_features()
        assert any(
            x["name"] == "BOLD_EdgeCentricFCMaps_functional_connectivity"
            for x in features.values()
        )
