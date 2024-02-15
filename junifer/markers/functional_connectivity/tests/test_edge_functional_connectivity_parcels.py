"""Provide tests for edge-centric functional connectivity using parcels."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

from junifer.datareader import DefaultDataReader
from junifer.markers.functional_connectivity import EdgeCentricFCParcels
from junifer.storage import SQLiteFeatureStorage
from junifer.testing.datagrabbers import PartlyCloudyTestingDataGrabber


def test_EdgeCentricFCParcels(tmp_path: Path) -> None:
    """Test EdgeCentricFCParcels.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with PartlyCloudyTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        marker = EdgeCentricFCParcels(
            parcellation="TianxS1x3TxMNInonlinear2009cAsym",
            cor_method_params={"empirical": True},
        )
        # Check correct output
        assert marker.get_output_type("BOLD") == "matrix"

        # Fit-transform the data
        edge_fc = marker.fit_transform(element_data)
        edge_fc_bold = edge_fc["BOLD"]

        # For 16 ROIs we should get (16 * (16 -1) / 2) edges in the ETS
        n_edges = int(16 * (16 - 1) / 2)
        assert "data" in edge_fc_bold
        assert "row_names" in edge_fc_bold
        assert "col_names" in edge_fc_bold
        assert edge_fc_bold["data"].shape[0] == n_edges
        assert edge_fc_bold["data"].shape[1] == n_edges
        assert len(set(edge_fc_bold["row_names"])) == n_edges
        assert len(set(edge_fc_bold["col_names"])) == n_edges

        # Store
        storage = SQLiteFeatureStorage(
            uri=tmp_path / "test_edge_fc_parcels.sqlite", upsert="ignore"
        )
        marker.fit_transform(input=element_data, storage=storage)
        features = storage.list_features()
        assert any(
            x["name"] == "BOLD_EdgeCentricFCParcels" for x in features.values()
        )
