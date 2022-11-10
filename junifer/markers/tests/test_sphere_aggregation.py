"""Provide tests for sphere aggregation."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from pathlib import Path

import nibabel as nib
import pytest
from nilearn import datasets
from nilearn.image import concat_imgs
from nilearn.maskers import NiftiSpheresMasker
from numpy.testing import assert_array_equal

from junifer.data import load_coordinates
from junifer.markers.sphere_aggregation import SphereAggregation
from junifer.storage import SQLiteFeatureStorage


def test_SphereAggregation_input_output() -> None:
    """Test SphereAggregation input and output types."""
    marker = SphereAggregation(
        coords="DMNBuckner", method="mean", radius=8, on="VBM_GM"
    )

    output = marker.get_output_kind(["VBM_GM", "BOLD"])
    assert output == ["table", "timeseries"]

    with pytest.raises(ValueError, match="Unknown input"):
        marker.get_output_kind(["VBM_GM", "BOLD", "unknown"])


def test_SphereAggregation_3D() -> None:
    """Test SphereAggregation object on 3D images."""
    # Get the testing coordinates (for nilearn)
    coord_names = "DMNBuckner"
    radius = 8
    coordinates, labels = load_coordinates(coord_names)

    # Get the oasis VBM data
    oasis_dataset = datasets.fetch_oasis_vbm(n_subjects=1)
    vbm = oasis_dataset.gray_matter_maps[0]
    img = nib.load(vbm)

    # Create NiftiLabelsMasker
    nifti_masker = NiftiSpheresMasker(seeds=coordinates, radius=radius)
    auto4d = nifti_masker.fit_transform(img)

    # Create SphereAggregation object
    marker = SphereAggregation(
        coords=coord_names, method="mean", radius=radius, on="VBM_GM"
    )
    input = {"VBM_GM": {"data": img}}
    jun_values4d = marker.fit_transform(input)["VBM_GM"]["data"]

    assert jun_values4d.ndim == 2
    assert_array_equal(auto4d.shape, jun_values4d.shape)
    assert_array_equal(auto4d, jun_values4d)

    meta = marker.get_meta("VBM_GM")["marker"]
    assert meta["method"] == "mean"
    assert meta["coords"] == coord_names
    assert meta["radius"] == radius
    assert meta["name"] == "VBM_GM_SphereAggregation"
    assert meta["class"] == "SphereAggregation"
    assert meta["kind"] == "VBM_GM"
    assert meta["method_params"] == {}

    with pytest.raises(NotImplementedError, match="mean aggregation"):
        marker = SphereAggregation(
            coords=coord_names, method="std", radius=radius, on="BOLD"
        )


def test_SphereAggregation_4D() -> None:
    """Test SphereAggregation object on 4D images."""
    # Get the testing coordinates (for nilearn)
    coord_names = "DMNBuckner"
    radius = 8
    coordinates, labels = load_coordinates(coord_names)

    # Get the SPM auditory data:
    subject_data = datasets.fetch_spm_auditory()
    fmri_img = concat_imgs(subject_data.func)  # type: ignore

    # Create NiftiLabelsMasker
    nifti_masker = NiftiSpheresMasker(seeds=coordinates, radius=radius)
    auto4d = nifti_masker.fit_transform(fmri_img)

    # Create SphereAggregation object
    marker = SphereAggregation(coords=coord_names, method="mean", radius=radius)
    input = {"BOLD": {"data": fmri_img}}
    jun_values4d = marker.fit_transform(input)["BOLD"]["data"]

    assert jun_values4d.ndim == 2
    assert_array_equal(auto4d.shape, jun_values4d.shape)
    assert_array_equal(auto4d, jun_values4d)

    meta = marker.get_meta("BOLD")["marker"]
    assert meta["method"] == "mean"
    assert meta["coords"] == coord_names
    assert meta["radius"] == radius
    assert meta["name"] == "BOLD_SphereAggregation"
    assert meta["class"] == "SphereAggregation"
    assert meta["kind"] == "BOLD"
    assert meta["method_params"] == {}


def test_SphereAggregation_storage(tmp_path: Path) -> None:
    """Test SphereAggregation storage.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    # Get the oasis VBM data
    oasis_dataset = datasets.fetch_oasis_vbm(n_subjects=1)
    vbm = oasis_dataset.gray_matter_maps[0]
    img = nib.load(vbm)
    uri = tmp_path / "test_sphere_storage_3D.db"

    storage = SQLiteFeatureStorage(uri=uri, single_output=True, upsert="ignore")
    meta = {
        "element": "test",
        "version": "0.0.1",
        "marker": {"name": "fcname"},
    }
    input = {"VBM_GM": {"data": img}, "meta": meta}
    marker = SphereAggregation(
        coords="DMNBuckner", method="mean", radius=8, on="VBM_GM"
    )

    marker.fit_transform(input, storage=storage)

    meta = {
        "element": "test",
        "version": "0.0.1",
        "marker": {"name": "BOLD_fcname"},
    }
    # Get the SPM auditory data:
    subject_data = datasets.fetch_spm_auditory()
    fmri_img = concat_imgs(subject_data.func)  # type: ignore
    input = {"BOLD": {"data": fmri_img}, "meta": meta}
    marker = SphereAggregation(coords="DMNBuckner", method="mean", radius=8, on="BOLD")

    marker.fit_transform(input, storage=storage)
