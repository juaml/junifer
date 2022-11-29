"""Provide tests for functional connectivity spheres."""

# Authors: Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Kaustubh R. Patil <k.patil@fz-juelich.de>
#          Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from pathlib import Path

import pytest
from nilearn import datasets, image
from nilearn.connectome import ConnectivityMeasure
from numpy.testing import assert_array_almost_equal
from sklearn.covariance import EmpiricalCovariance

from junifer.markers.functional_connectivity_spheres import (
    FunctionalConnectivitySpheres,
)
from junifer.markers.sphere_aggregation import SphereAggregation
from junifer.storage import SQLiteFeatureStorage


def test_FunctionalConnectivitySpheres(tmp_path: Path) -> None:
    """Test FunctionalConnectivitySpheres.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    # get a dataset
    ni_data = datasets.fetch_spm_auditory(subject_id="sub001")
    fmri_img = image.concat_imgs(ni_data.func)  # type: ignore

    fc = FunctionalConnectivitySpheres(
        coords="DMNBuckner", radius=5.0, cor_method="correlation"
    )
    all_out = fc.fit_transform({"BOLD": {"data": fmri_img, "meta": {}}})

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
    ts = sa.compute({"data": fmri_img, "meta": {}})

    # Check that FC are almost equal when using nileran
    cm = ConnectivityMeasure(kind="correlation")
    out_ni = cm.fit_transform([ts["data"]])[0]
    assert_array_almost_equal(out_ni, out["data"], decimal=3)

    # check correct output
    assert fc.get_output_type("BOLD") == "matrix"

    uri = tmp_path / "test_fc_parcel.sqlite"
    # Single storage, must be the uri
    storage = SQLiteFeatureStorage(uri=uri, upsert="ignore")
    meta = {
        "element": {"subject": "test"},
        "dependencies": {"numpy", "nilearn"},
    }
    input = {"BOLD": {"data": fmri_img, "meta": meta}}
    all_out = fc.fit_transform(input, storage=storage)

    features = storage.list_features()
    assert any(
        x["name"] == "BOLD_FunctionalConnectivitySpheres"
        for x in features.values()
    )


def test_FunctionalConnectivitySpheres_empirical(tmp_path: Path) -> None:
    """Test FunctionalConnectivitySpheres with empirical covariance.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """

    # get a dataset
    ni_data = datasets.fetch_spm_auditory(subject_id="sub001")
    fmri_img = image.concat_imgs(ni_data.func)  # type: ignore

    fc = FunctionalConnectivitySpheres(
        coords="DMNBuckner",
        radius=5.0,
        cor_method="correlation",
        cor_method_params={"empirical": True},
    )
    all_out = fc.fit_transform({"BOLD": {"data": fmri_img, "meta": {}}})

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

    # Check that FC are almost equal when using nileran
    cm = ConnectivityMeasure(
        cov_estimator=EmpiricalCovariance(), kind="correlation"  # type: ignore
    )
    out_ni = cm.fit_transform([ts["data"]])[0]
    assert_array_almost_equal(out_ni, out["data"], decimal=3)


def test_FunctionalConnectivitySpheres_error() -> None:
    """Test FunctionalConnectivitySpheres errors."""
    with pytest.raises(ValueError, match="radius should be > 0"):
        FunctionalConnectivitySpheres(
            coords="DMNBuckner", radius=-0.1, cor_method="correlation"
        )
