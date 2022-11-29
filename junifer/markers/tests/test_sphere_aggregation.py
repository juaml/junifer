"""Provide tests for sphere aggregation."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

import typing
from pathlib import Path
from typing import Dict

import nibabel as nib
import pytest
from nilearn import datasets
from nilearn.image import concat_imgs
from nilearn.maskers import NiftiSpheresMasker
from numpy.testing import assert_array_equal

from junifer.data import load_coordinates, load_mask
from junifer.markers.sphere_aggregation import SphereAggregation
from junifer.storage import SQLiteFeatureStorage


# Define common variables
COORDS = "DMNBuckner"
RADIUS = 8


def test_SphereAggregation_input_output() -> None:
    """Test SphereAggregation input and output types."""
    marker = SphereAggregation(coords="DMNBuckner", method="mean", on="VBM_GM")
    for in_, out_ in [("VBM_GM", "table"), ("BOLD", "timeseries")]:
        assert marker.get_output_type(in_) == out_

    with pytest.raises(ValueError, match="Unknown input"):
        marker.get_output_type("unknown")


def test_SphereAggregation_3D() -> None:
    """Test SphereAggregation object on 3D images."""
    # Get the testing coordinates (for nilearn)
    coordinates, labels = load_coordinates(COORDS)

    # Get the oasis VBM data
    oasis_dataset = datasets.fetch_oasis_vbm(n_subjects=1)
    vbm = oasis_dataset.gray_matter_maps[0]
    img = nib.load(vbm)

    # Create NiftSpheresMasker
    nifti_masker = NiftiSpheresMasker(seeds=coordinates, radius=RADIUS)
    auto4d = nifti_masker.fit_transform(img)

    # Create SphereAggregation object
    marker = SphereAggregation(
        coords=COORDS, method="mean", radius=RADIUS, on="VBM_GM"
    )
    input = {"VBM_GM": {"data": img, "meta": {}}}
    jun_values4d = marker.fit_transform(input)["VBM_GM"]["data"]

    assert jun_values4d.ndim == 2
    assert_array_equal(auto4d.shape, jun_values4d.shape)
    assert_array_equal(auto4d, jun_values4d)


def test_SphereAggregation_4D() -> None:
    """Test SphereAggregation object on 4D images."""
    # Get the testing coordinates (for nilearn)
    coordinates, _ = load_coordinates(COORDS)

    # Get the SPM auditory data
    subject_data = datasets.fetch_spm_auditory()
    fmri_img = concat_imgs(subject_data.func)  # type: ignore

    # Create NiftSpheresMasker
    nifti_masker = NiftiSpheresMasker(seeds=coordinates, radius=RADIUS)
    auto4d = nifti_masker.fit_transform(fmri_img)

    # Create SphereAggregation object
    marker = SphereAggregation(coords=COORDS, method="mean", radius=RADIUS)
    input = {"BOLD": {"data": fmri_img, "meta": {}}}
    jun_values4d = marker.fit_transform(input)["BOLD"]["data"]

    assert jun_values4d.ndim == 2
    assert_array_equal(auto4d.shape, jun_values4d.shape)
    assert_array_equal(auto4d, jun_values4d)


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
    uri = tmp_path / "test_sphere_storage_3D.sqlite"

    storage = SQLiteFeatureStorage(uri=uri, upsert="ignore")
    meta = {
        "element": {"subject": "sub-01", "session": "ses-01"},
        "dependencies": {"nilearn", "nibabel"},
    }
    input = {"VBM_GM": {"data": img, "meta": meta}}
    marker = SphereAggregation(
        coords=COORDS, method="mean", radius=RADIUS, on="VBM_GM"
    )

    marker.fit_transform(input, storage=storage)

    features: Dict = typing.cast(Dict, storage.list_features())
    assert any(
        x["name"] == "VBM_GM_SphereAggregation" for x in features.values()
    )

    meta = {
        "element": {"subject": "sub-01", "session": "ses-01"},
        "dependencies": {"nilearn", "nibabel"},
    }
    # Get the SPM auditory data
    subject_data = datasets.fetch_spm_auditory()
    fmri_img = concat_imgs(subject_data.func)  # type: ignore
    input = {"BOLD": {"data": fmri_img, "meta": meta}}
    marker = SphereAggregation(
        coords=COORDS, method="mean", radius=RADIUS, on="BOLD"
    )

    marker.fit_transform(input, storage=storage)
    features: Dict = typing.cast(Dict, storage.list_features())
    assert any(
        x["name"] == "BOLD_SphereAggregation" for x in features.values()
    )


def test_SphereAggregation_3D_mask() -> None:
    """Test SphereAggregation object on 3D images using mask."""
    # Get the testing coordinates (for nilearn)
    coordinates, _ = load_coordinates(COORDS)

    # Get one mask
    mask_img, _ = load_mask("GM_prob0.2")

    # Get the oasis VBM data
    oasis_dataset = datasets.fetch_oasis_vbm(n_subjects=1)
    vbm = oasis_dataset.gray_matter_maps[0]
    img = nib.load(vbm)

    # Create NiftSpheresMasker
    nifti_masker = NiftiSpheresMasker(
        seeds=coordinates, radius=RADIUS, mask_img=mask_img
    )
    auto4d = nifti_masker.fit_transform(img)

    # Create SphereAggregation object
    marker = SphereAggregation(
        coords=COORDS,
        method="mean",
        radius=RADIUS,
        on="VBM_GM",
        mask="GM_prob0.2",
    )
    input = {"VBM_GM": {"data": img, "meta": {}}}
    jun_values4d = marker.fit_transform(input)["VBM_GM"]["data"]

    assert jun_values4d.ndim == 2
    assert_array_equal(auto4d.shape, jun_values4d.shape)
    assert_array_equal(auto4d, jun_values4d)
