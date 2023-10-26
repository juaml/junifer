"""Provide tests for edge-centric functional connectivity using spheres."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

from nilearn import datasets, image

from junifer.markers.functional_connectivity import EdgeCentricFCSpheres
from junifer.storage import SQLiteFeatureStorage


def test_EdgeCentricFCSpheres(tmp_path: Path) -> None:
    """Test EdgeCentricFCSpheres.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    # get a dataset
    ni_data = datasets.fetch_spm_auditory(subject_id="sub001")
    fmri_img = image.concat_imgs(ni_data.func)  # type: ignore

    efc = EdgeCentricFCSpheres(
        coords="DMNBuckner", radius=5.0, cor_method="correlation"
    )
    all_out = efc.fit_transform(
        {"BOLD": {"data": fmri_img, "meta": {}, "space": "MNI"}}
    )

    out = all_out["BOLD"]

    # There are six DMNBuckner coordinates, so
    # for 6 ROIs we should get (6 * (6 -1) / 2) edges in the ETS
    n_edges = int(6 * (6 - 1) / 2)
    assert "data" in out
    assert "row_names" in out
    assert "col_names" in out
    assert out["data"].shape[0] == n_edges
    assert out["data"].shape[1] == n_edges
    assert len(set(out["row_names"])) == n_edges
    assert len(set(out["col_names"])) == n_edges

    # check correct output
    assert efc.get_output_type("BOLD") == "matrix"

    # Check empirical correlation method parameters
    efc = EdgeCentricFCSpheres(
        coords="DMNBuckner",
        radius=5.0,
        cor_method="correlation",
        cor_method_params={"empirical": True},
    )

    meta = {
        "element": {"subject": "sub001"},
        "dependencies": {"nilearn"},
    }
    all_out = efc.fit_transform(
        {"BOLD": {"data": fmri_img, "meta": meta, "space": "MNI"}}
    )

    uri = tmp_path / "test_fc_parcellation.sqlite"
    # Single storage, must be the uri
    storage = SQLiteFeatureStorage(uri=uri, upsert="ignore")
    meta = {"element": {"subject": "test"}, "dependencies": {"numpy"}}
    input = {"BOLD": {"data": fmri_img, "meta": meta, "space": "MNI"}}
    all_out = efc.fit_transform(input, storage=storage)

    features = storage.list_features()
    assert any(
        x["name"] == "BOLD_EdgeCentricFCSpheres" for x in features.values()
    )
