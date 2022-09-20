"""Provide test for parcel aggregation."""

# Authors: Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Kaustubh R. Patil <k.patil@fz-juelich.de>
# License: AGPL

from pathlib import Path

from nilearn import datasets, image
from nilearn.connectome import ConnectivityMeasure
from nilearn.maskers import NiftiLabelsMasker
from numpy.testing import assert_array_almost_equal, assert_array_equal

from junifer.markers.functional_connectivity_atlas import (
    FunctionalConnectivityAtlas,
)
from junifer.markers.parcel import ParcelAggregation
from junifer.storage import SQLiteFeatureStorage


def test_FunctionalConnectivityAtlas(tmp_path: Path) -> None:
    """Test FunctionalConnectivityAtlas."""

    # get a dataset
    ni_data = datasets.fetch_spm_auditory(subject_id="sub001")
    fmri_img = image.concat_imgs(ni_data.func)  # type: ignore

    fc = FunctionalConnectivityAtlas(atlas="Schaefer100x7")
    all_out = fc.fit_transform({"BOLD": {"data": fmri_img}})

    out = all_out["BOLD"]

    assert "data" in out
    assert "row_names" in out
    assert "col_names" in out
    assert out["data"].shape[0] == 100
    assert out["data"].shape[1] == 100
    assert len(set(out["row_names"])) == 100
    assert len(set(out["col_names"])) == 100

    # get the timeseries using pa
    pa = ParcelAggregation(atlas="Schaefer100x7", method="mean", on="BOLD")
    ts = pa.compute({"data": fmri_img})

    # compare with nilearn
    # Get the testing atlas (for nilearn)
    atlas = datasets.fetch_atlas_schaefer_2018(
        n_rois=100, yeo_networks=7, resolution_mm=2
    )
    masker = NiftiLabelsMasker(labels_img=atlas["maps"], standardize=False)
    ts_ni = masker.fit_transform(fmri_img)

    # check the TS are almost equal
    assert_array_equal(ts_ni, ts["data"])

    # Check that FC are almost equal
    cm = ConnectivityMeasure(kind="covariance")
    out_ni = cm.fit_transform([ts_ni])[0]
    assert_array_almost_equal(out_ni, out["data"], decimal=3)

    # check correct output
    assert fc.get_output_kind(["BOLD"]) == ["matrix"]

    # Check empirical correlation method parameters
    fc = FunctionalConnectivityAtlas(
        atlas="Schaefer100x7", cor_method_params={"empirical": True}
    )

    all_out = fc.fit_transform({"BOLD": {"data": fmri_img}})

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
