"""Provide tests for edge-centric functional connectivity using parcels."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import Dict

import pytest

from junifer.datareader import DefaultDataReader
from junifer.markers.functional_connectivity import EdgeCentricFCParcels
from junifer.storage import SQLiteFeatureStorage
from junifer.testing.datagrabbers import PartlyCloudyTestingDataGrabber


@pytest.mark.parametrize(
    "conn_method_params",
    [
        {"empirical": False},
        {"empirical": True},
    ],
)
def test_EdgeCentricFCParcels(
    tmp_path: Path,
    conn_method_params: Dict[str, bool],
) -> None:
    """Test EdgeCentricFCParcels.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    conn_method_params : dict
        The parametrized parameters to connectivity measure method.

    """
    with PartlyCloudyTestingDataGrabber() as dg:
        # Get element data
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        # Setup marker
        marker = EdgeCentricFCParcels(
            parcellation="TianxS1x3TxMNInonlinear2009cAsym",
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

        # For 16 ROIs we should get (16 * (16 -1) / 2) edges in the ETS
        n_edges = int(16 * (16 - 1) / 2)
        assert "data" in edge_fc_bold
        assert "row_names" in edge_fc_bold
        assert "col_names" in edge_fc_bold
        assert edge_fc_bold["data"].shape == (n_edges, n_edges)
        assert len(set(edge_fc_bold["row_names"])) == n_edges
        assert len(set(edge_fc_bold["col_names"])) == n_edges

        # Store
        storage = SQLiteFeatureStorage(
            uri=tmp_path / "test_edge_fc_parcels.sqlite", upsert="ignore"
        )
        marker.fit_transform(input=element_data, storage=storage)
        features = storage.list_features()
        assert any(
            x["name"] == "BOLD_EdgeCentricFCParcels_functional_connectivity"
            for x in features.values()
        )
