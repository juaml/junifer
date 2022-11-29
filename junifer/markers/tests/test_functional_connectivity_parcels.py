"""Provide tests for functional connectivity using parcellation."""

# Authors: Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Kaustubh R. Patil <k.patil@fz-juelich.de>
# License: AGPL

from pathlib import Path

from nilearn import datasets, image
from nilearn.connectome import ConnectivityMeasure
from nilearn.maskers import NiftiLabelsMasker
from numpy.testing import assert_array_almost_equal, assert_array_equal

from junifer.markers.functional_connectivity_parcels import (
    FunctionalConnectivityParcels,
)
from junifer.markers.parcel_aggregation import ParcelAggregation
from junifer.storage import SQLiteFeatureStorage


def test_FunctionalConnectivityParcels(tmp_path: Path) -> None:
    """Test FunctionalConnectivityParcels.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    # get a dataset
    ni_data = datasets.fetch_spm_auditory(subject_id="sub001")
    fmri_img = image.concat_imgs(ni_data.func)  # type: ignore

    fc = FunctionalConnectivityParcels(parcellation="Schaefer100x7")
    all_out = fc.fit_transform({"BOLD": {"data": fmri_img, "meta": {}}})

    out = all_out["BOLD"]

    assert "data" in out
    assert "row_names" in out
    assert "col_names" in out
    assert out["data"].shape[0] == 100
    assert out["data"].shape[1] == 100
    assert len(set(out["row_names"])) == 100
    assert len(set(out["col_names"])) == 100

    # get the timeseries using pa
    pa = ParcelAggregation(
        parcellation="Schaefer100x7", method="mean", on="BOLD"
    )
    meta = {
        "element": {"subject": "sub001"},
        "dependencies": {"nilearn"},
    }
    ts = pa.compute({"data": fmri_img, "meta": meta})

    # compare with nilearn
    # Get the testing parcellation (for nilearn)
    parcellation = datasets.fetch_atlas_schaefer_2018(
        n_rois=100, yeo_networks=7, resolution_mm=2
    )
    masker = NiftiLabelsMasker(
        labels_img=parcellation["maps"], standardize=False
    )
    ts_ni = masker.fit_transform(fmri_img)

    # check the TS are almost equal
    assert_array_equal(ts_ni, ts["data"])

    # Check that FC are almost equal
    cm = ConnectivityMeasure(kind="covariance")
    out_ni = cm.fit_transform([ts_ni])[0]
    assert_array_almost_equal(out_ni, out["data"], decimal=3)

    # check correct output
    assert fc.get_output_type("BOLD") == "matrix"

    # Check empirical correlation method parameters
    fc = FunctionalConnectivityParcels(
        parcellation="Schaefer100x7", cor_method_params={"empirical": True}
    )

    all_out = fc.fit_transform({"BOLD": {"data": fmri_img, "meta": meta}})

    uri = tmp_path / "test_fc_parcellation.sqlite"
    # Single storage, must be the uri
    storage = SQLiteFeatureStorage(uri=uri, upsert="ignore")
    meta = {"element": {"subject": "test"}, "dependencies": {"numpy"}}
    input = {"BOLD": {"data": fmri_img, "meta": meta}}
    all_out = fc.fit_transform(input, storage=storage)

    features = storage.list_features()
    assert any(
        x["name"] == "BOLD_FunctionalConnectivityParcels"
        for x in features.values()
    )
