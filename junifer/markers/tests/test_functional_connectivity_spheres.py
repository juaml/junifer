"""Provide test for parcel aggregation."""

# Authors: Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Kaustubh R. Patil <k.patil@fz-juelich.de>
#          Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
from pathlib import Path
from numpy.testing import assert_array_almost_equal

from nilearn import datasets, image
from nilearn.connectome import ConnectivityMeasure

from junifer.markers.functional_connectivity_spheres import (
    FunctionalConnectivitySpheres,
)
from junifer.markers.sphere_aggregation import SphereAggregation
from junifer.storage import SQLiteFeatureStorage


def test_FunctionalConnectivitySpheres(tmp_path: Path) -> None:
    """Test FunctionalConnectivitySpheres."""

    # get a dataset
    ni_data = datasets.fetch_spm_auditory(subject_id="sub001")
    fmri_img = image.concat_imgs(ni_data.func)  # type: ignore

    fc = FunctionalConnectivitySpheres(
        coords="DMNBuckner", radius=5.0, cor_method="correlation"
    )
    all_out = fc.fit_transform({"BOLD": {"data": fmri_img}})

    out = all_out["BOLD"]

    assert "data" in out
    assert "row_names" in out
    assert "col_names" in out
    assert out["data"].shape[0] == 6
    assert out["data"].shape[1] == 6
    assert len(set(out["row_names"])) == 6
    assert len(set(out["col_names"])) == 6

    # get the timeseries using sa
    sa = SphereAggregation(
        coords="DMNBuckner", radius=5.0, method="mean", on="BOLD"
    )
    ts = sa.compute({"data": fmri_img})

    # compare with nilearn

    # Check that FC are almost equal
    cm = ConnectivityMeasure(kind="correlation")
    out_ni = cm.fit_transform([ts["data"]])[0]
    assert_array_almost_equal(out_ni, out["data"], decimal=3)

    # check correct output
    assert fc.get_output_kind(["BOLD"]) == ["matrix"]

    uri = tmp_path / "test_fc_atlas.db"
    # Single storage, must be the uri
    storage = SQLiteFeatureStorage(
        uri=uri, single_output=True, upsert="ignore"
    )
    meta = {
        "element": "test",
        "version": "0.0.1",
        "marker": {"name": "fcname"},
    }
    input = {"BOLD": {"data": fmri_img}, "meta": meta}
    all_out = fc.fit_transform(input, storage=storage)
