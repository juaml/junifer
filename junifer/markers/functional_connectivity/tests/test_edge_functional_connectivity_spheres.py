"""Provide tests for edge-centric functional connectivity using spheres."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

from junifer.datareader import DefaultDataReader
from junifer.markers.functional_connectivity import EdgeCentricFCSpheres
from junifer.storage import SQLiteFeatureStorage
from junifer.testing.datagrabbers import SPMAuditoryTestingDataGrabber


def test_EdgeCentricFCSpheres(tmp_path: Path) -> None:
    """Test EdgeCentricFCSpheres.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with SPMAuditoryTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub001"])
        marker = EdgeCentricFCSpheres(
            coords="DMNBuckner", radius=5.0, cor_method="correlation"
        )
        # Check correct output
        assert marker.get_output_type("BOLD") == "matrix"

        # Fit-transform the data
        edge_fc = marker.fit_transform(element_data)
        edge_fc_bold = edge_fc["BOLD"]

        # There are six DMNBuckner coordinates, so
        # for 6 ROIs we should get (6 * (6 -1) / 2) edges in the ETS
        n_edges = int(6 * (6 - 1) / 2)
        assert "data" in edge_fc_bold
        assert "row_names" in edge_fc_bold
        assert "col_names" in edge_fc_bold
        assert edge_fc_bold["data"].shape == (n_edges, n_edges)
        assert len(set(edge_fc_bold["row_names"])) == n_edges
        assert len(set(edge_fc_bold["col_names"])) == n_edges

        # Check empirical correlation method parameters
        marker = EdgeCentricFCSpheres(
            coords="DMNBuckner",
            radius=5.0,
            cor_method="correlation",
            cor_method_params={"empirical": True},
        )
        # Store
        storage = SQLiteFeatureStorage(
            uri=tmp_path / "test_edge_fc_spheres.sqlite", upsert="ignore"
        )
        marker.fit_transform(input=element_data, storage=storage)
        features = storage.list_features()
        assert any(
            x["name"] == "BOLD_EdgeCentricFCSpheres" for x in features.values()
        )
