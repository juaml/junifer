"""Provide test for parcel aggregation."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import warnings
from pathlib import Path

import nibabel as nib
import numpy as np
import pytest
from nilearn import datasets
from nilearn.image import concat_imgs, math_img, new_img_like, resample_to_img
from nilearn.maskers import NiftiLabelsMasker, NiftiMasker
from nilearn.masking import compute_brain_mask
from numpy.testing import assert_array_almost_equal, assert_array_equal
from scipy.stats import trim_mean

from junifer.data import load_mask, load_parcellation, register_parcellation
from junifer.markers.parcel_aggregation import ParcelAggregation
from junifer.storage import SQLiteFeatureStorage


def test_ParcelAggregation_input_output() -> None:
    """Test ParcelAggregation input and output types."""
    marker = ParcelAggregation(
        parcellation="Schaefer100x7", method="mean", on="VBM_GM"
    )
    for in_, out_ in [("VBM_GM", "vector"), ("BOLD", "timeseries")]:
        assert marker.get_output_type(in_) == out_

    with pytest.raises(ValueError, match="Unknown input"):
        marker.get_output_type("unknown")


def test_ParcelAggregation_3D() -> None:
    """Test ParcelAggregation object on 3D images."""
    # Get the testing parcellation (for nilearn)
    parcellation = datasets.fetch_atlas_schaefer_2018(n_rois=100)

    # Get the oasis VBM data
    oasis_dataset = datasets.fetch_oasis_vbm(n_subjects=1)
    vbm = oasis_dataset.gray_matter_maps[0]
    img = nib.load(vbm)

    # Mask parcellation manually
    parcellation_img_res = resample_to_img(
        parcellation.maps,
        img,
        interpolation="nearest",
    )
    parcellation_bin = math_img(
        "img != 0",
        img=parcellation_img_res,
    )

    # Create NiftiMasker
    masker = NiftiMasker(parcellation_bin, target_affine=img.affine)
    data = masker.fit_transform(img)
    parcellation_values = masker.transform(parcellation_img_res)
    parcellation_values = np.squeeze(parcellation_values).astype(int)

    # Compute the mean manually
    manual = []
    for t_v in sorted(np.unique(parcellation_values)):
        t_values = np.mean(data[:, parcellation_values == t_v])
        manual.append(t_values)
    manual = np.array(manual)[np.newaxis, :]

    # Create NiftiLabelsMasker
    nifti_masker = NiftiLabelsMasker(labels_img=parcellation.maps)
    auto = nifti_masker.fit_transform(img)

    # Check that arrays are almost equal
    assert_array_almost_equal(auto, manual)

    # Use the ParcelAggregation object
    marker = ParcelAggregation(
        parcellation="Schaefer100x7",
        method="mean",
        name="gmd_schaefer100x7_mean",
        on="VBM_GM",
    )  # Test passing "on" as a keyword argument
    input = {"VBM_GM": {"data": img, "meta": {}, "space": "MNI"}}
    jun_values3d_mean = marker.fit_transform(input)["VBM_GM"]["data"]

    assert jun_values3d_mean.ndim == 2
    assert jun_values3d_mean.shape[0] == 1
    assert_array_equal(manual, jun_values3d_mean)

    # Test using another function (std)
    manual = []
    for t_v in sorted(np.unique(parcellation_values)):
        t_values = np.std(data[:, parcellation_values == t_v])
        manual.append(t_values)
    manual = np.array(manual)[np.newaxis, :]

    # Use the ParcelAggregation object
    marker = ParcelAggregation(parcellation="Schaefer100x7", method="std")
    input = {"VBM_GM": {"data": img, "meta": {}, "space": "MNI"}}
    jun_values3d_std = marker.fit_transform(input)["VBM_GM"]["data"]

    assert jun_values3d_std.ndim == 2
    assert jun_values3d_std.shape[0] == 1
    assert_array_equal(manual, jun_values3d_std)

    # Test using another function with parameters
    manual = []
    for t_v in sorted(np.unique(parcellation_values)):
        t_values = trim_mean(
            data[:, parcellation_values == t_v],
            proportiontocut=0.1,
            axis=None,  # type: ignore
        )
        manual.append(t_values)
    manual = np.array(manual)[np.newaxis, :]

    # Use the ParcelAggregation object
    marker = ParcelAggregation(
        parcellation="Schaefer100x7",
        method="trim_mean",
        method_params={"proportiontocut": 0.1},
    )
    input = {"VBM_GM": {"data": img, "meta": {}, "space": "MNI"}}
    jun_values3d_tm = marker.fit_transform(input)["VBM_GM"]["data"]

    assert jun_values3d_tm.ndim == 2
    assert jun_values3d_tm.shape[0] == 1
    assert_array_equal(manual, jun_values3d_tm)


def test_ParcelAggregation_4D():
    """Test ParcelAggregation object on 4D images."""
    # Get the testing parcellation (for nilearn)
    parcellation = datasets.fetch_atlas_schaefer_2018(
        n_rois=100, yeo_networks=7, resolution_mm=2
    )

    # Get the SPM auditory data:
    subject_data = datasets.fetch_spm_auditory()
    fmri_img = concat_imgs(subject_data.func)  # type: ignore

    # Create NiftiLabelsMasker
    nifti_masker = NiftiLabelsMasker(labels_img=parcellation.maps)
    auto4d = nifti_masker.fit_transform(fmri_img)

    # Create ParcelAggregation object
    marker = ParcelAggregation(parcellation="Schaefer100x7", method="mean")
    input = {"BOLD": {"data": fmri_img, "meta": {}, "space": "MNI"}}
    jun_values4d = marker.fit_transform(input)["BOLD"]["data"]

    assert jun_values4d.ndim == 2
    assert_array_equal(auto4d.shape, jun_values4d.shape)
    assert_array_equal(auto4d, jun_values4d)


def test_ParcelAggregation_storage(tmp_path: Path) -> None:
    """Test ParcelAggregation storage.

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
    input = {"VBM_GM": {"data": img, "meta": meta, "space": "MNI"}}
    marker = ParcelAggregation(
        parcellation="Schaefer100x7", method="mean", on="VBM_GM"
    )

    marker.fit_transform(input, storage=storage)

    features = storage.list_features()
    assert any(
        x["name"] == "VBM_GM_ParcelAggregation" for x in features.values()
    )

    meta = {
        "element": {"subject": "sub-01", "session": "ses-01"},
        "dependencies": {"nilearn", "nibabel"},
    }
    # Get the SPM auditory data
    subject_data = datasets.fetch_spm_auditory()
    fmri_img = concat_imgs(subject_data.func)  # type: ignore
    input = {"BOLD": {"data": fmri_img, "meta": meta, "space": "MNI"}}
    marker = ParcelAggregation(
        parcellation="Schaefer100x7", method="mean", on="BOLD"
    )

    marker.fit_transform(input, storage=storage)
    features = storage.list_features()
    assert any(
        x["name"] == "BOLD_ParcelAggregation" for x in features.values()
    )


def test_ParcelAggregation_3D_mask() -> None:
    """Test ParcelAggregation object on 3D images with mask."""

    # Get the testing parcellation (for nilearn)
    parcellation = datasets.fetch_atlas_schaefer_2018(n_rois=100)

    # Get one mask
    mask_img, _, _ = load_mask("GM_prob0.2")

    # Get the oasis VBM data
    oasis_dataset = datasets.fetch_oasis_vbm(n_subjects=1)
    vbm = oasis_dataset.gray_matter_maps[0]
    img = nib.load(vbm)

    # Create NiftiLabelsMasker
    nifti_masker = NiftiLabelsMasker(
        labels_img=parcellation.maps, mask_img=mask_img
    )
    auto = nifti_masker.fit_transform(img)

    # Use the ParcelAggregation object
    marker = ParcelAggregation(
        parcellation="Schaefer100x7",
        method="mean",
        masks="GM_prob0.2",
        name="gmd_schaefer100x7_mean",
        on="VBM_GM",
    )  # Test passing "on" as a keyword argument
    input = {"VBM_GM": {"data": img, "meta": {}, "space": "MNI"}}
    jun_values3d_mean = marker.fit_transform(input)["VBM_GM"]["data"]

    assert jun_values3d_mean.ndim == 2
    assert jun_values3d_mean.shape[0] == 1
    assert_array_almost_equal(auto, jun_values3d_mean)


def test_ParcelAggregation_3D_mask_computed() -> None:
    """Test ParcelAggregation object on 3D images with computed masks."""

    # Get the testing parcellation (for nilearn)
    parcellation = datasets.fetch_atlas_schaefer_2018(n_rois=100)

    # Get the oasis VBM data
    oasis_dataset = datasets.fetch_oasis_vbm(n_subjects=1)
    vbm = oasis_dataset.gray_matter_maps[0]
    img = nib.load(vbm)

    # Get one mask
    mask_img = compute_brain_mask(img, threshold=0.2)

    # Create NiftiLabelsMasker
    nifti_masker = NiftiLabelsMasker(
        labels_img=parcellation.maps, mask_img=mask_img
    )
    auto = nifti_masker.fit_transform(img)

    # Get one mask
    mask_img = compute_brain_mask(img, threshold=0.5)

    # Create NiftiLabelsMasker
    nifti_masker = NiftiLabelsMasker(
        labels_img=parcellation.maps, mask_img=mask_img
    )
    auto_bad = nifti_masker.fit_transform(img)

    # Use the ParcelAggregation object
    marker = ParcelAggregation(
        parcellation="Schaefer100x7",
        method="mean",
        masks={"compute_brain_mask": {"threshold": 0.2}},
        name="gmd_schaefer100x7_mean",
        on="VBM_GM",
    )  # Test passing "on" as a keyword argument
    input = {"VBM_GM": {"data": img, "meta": {}, "space": "MNI"}}
    jun_values3d_mean = marker.fit_transform(input)["VBM_GM"]["data"]

    assert jun_values3d_mean.ndim == 2
    assert jun_values3d_mean.shape[0] == 1
    assert_array_almost_equal(auto, jun_values3d_mean)

    with pytest.raises(AssertionError):
        assert_array_almost_equal(jun_values3d_mean, auto_bad)


def test_ParcelAggregation_3D_multiple_non_overlapping(tmp_path: Path) -> None:
    """Test ParcelAggregation with multiple non-overlapping parcellations.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """

    # Get the testing parcellation
    parcellation, labels, _, _ = load_parcellation("Schaefer100x7")

    assert parcellation is not None

    # Get the oasis VBM data
    oasis_dataset = datasets.fetch_oasis_vbm(n_subjects=1)
    vbm = oasis_dataset.gray_matter_maps[0]
    img = nib.load(vbm)

    # Create two parcellations from it
    parcellation_data = parcellation.get_fdata()
    parcellation1_data = parcellation_data.copy()
    parcellation1_data[parcellation1_data > 50] = 0
    parcellation2_data = parcellation_data.copy()
    parcellation2_data[parcellation2_data <= 50] = 0
    parcellation2_data[parcellation2_data > 0] -= 50
    labels1 = labels[:50]
    labels2 = labels[50:]

    parcellation1_img = new_img_like(parcellation, parcellation1_data)
    parcellation2_img = new_img_like(parcellation, parcellation2_data)

    parcellation1_path = tmp_path / "parcellation1.nii.gz"
    parcellation2_path = tmp_path / "parcellation2.nii.gz"

    nib.save(parcellation1_img, parcellation1_path)
    nib.save(parcellation2_img, parcellation2_path)

    register_parcellation(
        name="Schaefer100x7_low",
        parcellation_path=parcellation1_path,
        parcels_labels=labels1,
        space="MNI",
        overwrite=True,
    )
    register_parcellation(
        name="Schaefer100x7_high",
        parcellation_path=parcellation2_path,
        parcels_labels=labels2,
        space="MNI",
        overwrite=True,
    )

    # Use the ParcelAggregation object on the original parcellation
    marker_original = ParcelAggregation(
        parcellation="Schaefer100x7",
        method="mean",
        name="gmd_schaefer100x7_mean",
        on="VBM_GM",
    )  # Test passing "on" as a keyword argument
    input = {"VBM_GM": {"data": img, "meta": {}, "space": "MNI"}}
    orig_mean = marker_original.fit_transform(input)["VBM_GM"]

    orig_mean_data = orig_mean["data"]
    assert orig_mean_data.ndim == 2
    assert orig_mean_data.shape[0] == 1
    assert orig_mean_data.shape[1] == 100
    # assert_array_almost_equal(auto, jun_values3d_mean)

    # Use the ParcelAggregation object on the two parcellations
    marker_split = ParcelAggregation(
        parcellation=["Schaefer100x7_low", "Schaefer100x7_high"],
        method="mean",
        name="gmd_schaefer100x7_mean",
        on="VBM_GM",
    )  # Test passing "on" as a keyword argument
    input = {"VBM_GM": {"data": img, "meta": {}, "space": "MNI"}}

    # No warnings should be raised
    with warnings.catch_warnings():
        warnings.simplefilter("error", category=UserWarning)
        split_mean = marker_split.fit_transform(input)["VBM_GM"]
    split_mean_data = split_mean["data"]

    assert split_mean_data.ndim == 2
    assert split_mean_data.shape[0] == 1
    assert split_mean_data.shape[1] == 100

    # Data and labels should be the same
    assert_array_equal(orig_mean_data, split_mean_data)
    assert orig_mean["col_names"] == split_mean["col_names"]


def test_ParcelAggregation_3D_multiple_overlapping(tmp_path: Path) -> None:
    """Test ParcelAggregation with multiple overlapping parcellations.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """

    # Get the testing parcellation
    parcellation, labels, _, _ = load_parcellation("Schaefer100x7")

    assert parcellation is not None

    # Get the oasis VBM data
    oasis_dataset = datasets.fetch_oasis_vbm(n_subjects=1)
    vbm = oasis_dataset.gray_matter_maps[0]
    img = nib.load(vbm)

    # Create two parcellations from it
    parcellation_data = parcellation.get_fdata()
    parcellation1_data = parcellation_data.copy()
    parcellation1_data[parcellation1_data > 50] = 0
    parcellation2_data = parcellation_data.copy()

    # Make the second parcellation overlap with the first
    parcellation2_data[parcellation2_data <= 45] = 0
    parcellation2_data[parcellation2_data > 0] -= 45
    labels1 = [f"low_{x}" for x in labels[:50]]  # Change the labels
    labels2 = [f"high_{x}" for x in labels[45:]]  # Change the labels

    parcellation1_img = new_img_like(parcellation, parcellation1_data)
    parcellation2_img = new_img_like(parcellation, parcellation2_data)

    parcellation1_path = tmp_path / "parcellation1.nii.gz"
    parcellation2_path = tmp_path / "parcellation2.nii.gz"

    nib.save(parcellation1_img, parcellation1_path)
    nib.save(parcellation2_img, parcellation2_path)

    register_parcellation(
        name="Schaefer100x7_low2",
        parcellation_path=parcellation1_path,
        parcels_labels=labels1,
        space="MNI",
        overwrite=True,
    )
    register_parcellation(
        name="Schaefer100x7_high2",
        parcellation_path=parcellation2_path,
        parcels_labels=labels2,
        space="MNI",
        overwrite=True,
    )

    # Use the ParcelAggregation object on the original parcellation
    marker_original = ParcelAggregation(
        parcellation="Schaefer100x7",
        method="mean",
        name="gmd_schaefer100x7_mean",
        on="VBM_GM",
    )  # Test passing "on" as a keyword argument
    input = {"VBM_GM": {"data": img, "meta": {}, "space": "MNI"}}
    orig_mean = marker_original.fit_transform(input)["VBM_GM"]

    orig_mean_data = orig_mean["data"]
    assert orig_mean_data.ndim == 2
    assert orig_mean_data.shape[0] == 1
    assert orig_mean_data.shape[1] == 100
    # assert_array_almost_equal(auto, jun_values3d_mean)

    # Use the ParcelAggregation object on the two parcellations
    marker_split = ParcelAggregation(
        parcellation=["Schaefer100x7_low2", "Schaefer100x7_high2"],
        method="mean",
        name="gmd_schaefer100x7_mean",
        on="VBM_GM",
    )  # Test passing "on" as a keyword argument
    input = {"VBM_GM": {"data": img, "meta": {}, "space": "MNI"}}
    with pytest.warns(RuntimeWarning, match="overlapping voxels"):
        split_mean = marker_split.fit_transform(input)["VBM_GM"]
    split_mean_data = split_mean["data"]

    assert split_mean_data.ndim == 2
    assert split_mean_data.shape[0] == 1
    assert split_mean_data.shape[1] == 105

    # Overlapping voxels should be NaN
    assert np.isnan(split_mean_data[:, 50:55]).all()

    non_nan = split_mean_data[~np.isnan(split_mean_data)]
    # Data should be the same
    assert_array_equal(orig_mean_data, non_nan[None, :])

    # Labels should be "low" for the first 50 and "high" for the second 50
    assert all(x.startswith("low") for x in split_mean["col_names"][:50])
    assert all(x.startswith("high") for x in split_mean["col_names"][50:])


def test_ParcelAggregation_3D_multiple_duplicated_labels(
    tmp_path: Path,
) -> None:
    """Test ParcelAggregation with two parcellations with duplicated labels.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """

    # Get the testing parcellation
    parcellation, labels, _, _ = load_parcellation("Schaefer100x7")

    assert parcellation is not None

    # Get the oasis VBM data
    oasis_dataset = datasets.fetch_oasis_vbm(n_subjects=1)
    vbm = oasis_dataset.gray_matter_maps[0]
    img = nib.load(vbm)

    # Create two parcellations from it
    parcellation_data = parcellation.get_fdata()
    parcellation1_data = parcellation_data.copy()
    parcellation1_data[parcellation1_data > 50] = 0
    parcellation2_data = parcellation_data.copy()
    parcellation2_data[parcellation2_data <= 50] = 0
    parcellation2_data[parcellation2_data > 0] -= 50
    labels1 = labels[:50]
    labels2 = labels[49:-1]  # One label is duplicated

    parcellation1_img = new_img_like(parcellation, parcellation1_data)
    parcellation2_img = new_img_like(parcellation, parcellation2_data)

    parcellation1_path = tmp_path / "parcellation1.nii.gz"
    parcellation2_path = tmp_path / "parcellation2.nii.gz"

    nib.save(parcellation1_img, parcellation1_path)
    nib.save(parcellation2_img, parcellation2_path)

    register_parcellation(
        name="Schaefer100x7_low",
        parcellation_path=parcellation1_path,
        parcels_labels=labels1,
        space="MNI",
        overwrite=True,
    )
    register_parcellation(
        name="Schaefer100x7_high",
        parcellation_path=parcellation2_path,
        parcels_labels=labels2,
        space="MNI",
        overwrite=True,
    )

    # Use the ParcelAggregation object on the original parcellation
    marker_original = ParcelAggregation(
        parcellation="Schaefer100x7",
        method="mean",
        name="gmd_schaefer100x7_mean",
        on="VBM_GM",
    )  # Test passing "on" as a keyword argument
    input = {"VBM_GM": {"data": img, "meta": {}, "space": "MNI"}}
    orig_mean = marker_original.fit_transform(input)["VBM_GM"]

    orig_mean_data = orig_mean["data"]
    assert orig_mean_data.ndim == 2
    assert orig_mean_data.shape[0] == 1
    assert orig_mean_data.shape[1] == 100
    # assert_array_almost_equal(auto, jun_values3d_mean)

    # Use the ParcelAggregation object on the two parcellations
    marker_split = ParcelAggregation(
        parcellation=["Schaefer100x7_low", "Schaefer100x7_high"],
        method="mean",
        name="gmd_schaefer100x7_mean",
        on="VBM_GM",
    )  # Test passing "on" as a keyword argument
    input = {"VBM_GM": {"data": img, "meta": {}, "space": "MNI"}}

    with pytest.warns(RuntimeWarning, match="duplicated labels."):
        split_mean = marker_split.fit_transform(input)["VBM_GM"]
    split_mean_data = split_mean["data"]

    assert split_mean_data.ndim == 2
    assert split_mean_data.shape[0] == 1
    assert split_mean_data.shape[1] == 100

    # Data should be the same
    assert_array_equal(orig_mean_data, split_mean_data)

    # Labels should be prefixed with the parcellation name
    col_names = [f"Schaefer100x7_low_{x}" for x in labels1]
    col_names += [f"Schaefer100x7_high_{x}" for x in labels2]
    assert col_names == split_mean["col_names"]


def test_ParcelAggregation_4D_agg_time():
    """Test ParcelAggregation object on 4D images, aggregating time."""
    # Get the testing parcellation (for nilearn)
    parcellation = datasets.fetch_atlas_schaefer_2018(
        n_rois=100, yeo_networks=7, resolution_mm=2
    )

    # Get the SPM auditory data:
    subject_data = datasets.fetch_spm_auditory()
    fmri_img = concat_imgs(subject_data.func)  # type: ignore

    # Create NiftiLabelsMasker
    nifti_masker = NiftiLabelsMasker(labels_img=parcellation.maps)
    auto4d = nifti_masker.fit_transform(fmri_img)
    auto_mean = auto4d.mean(axis=0)

    # Create ParcelAggregation object
    marker = ParcelAggregation(
        parcellation="Schaefer100x7", method="mean", time_method="mean"
    )
    input = {"BOLD": {"data": fmri_img, "meta": {}, "space": "MNI"}}
    jun_values4d = marker.fit_transform(input)["BOLD"]["data"]

    assert jun_values4d.ndim == 1
    assert_array_equal(auto_mean.shape, jun_values4d.shape)
    assert_array_almost_equal(auto_mean, jun_values4d, decimal=2)

    auto_pick_0 = auto4d[:1, :]
    marker = ParcelAggregation(
        parcellation="Schaefer100x7",
        method="mean",
        time_method="select",
        time_method_params={"pick": [0]},
    )

    input = {"BOLD": {"data": fmri_img, "meta": {}, "space": "MNI"}}
    jun_values4d = marker.fit_transform(input)["BOLD"]["data"]

    assert jun_values4d.ndim == 2
    assert_array_equal(auto_pick_0.shape, jun_values4d.shape)
    assert_array_equal(auto_pick_0, jun_values4d)

    with pytest.raises(ValueError, match="can only be used with BOLD data"):
        ParcelAggregation(
            parcellation="Schaefer100x7",
            method="mean",
            time_method="select",
            time_method_params={"pick": [0]},
            on="VBM_GM",
        )

    with pytest.raises(
        ValueError, match="can only be used with `time_method`"
    ):
        ParcelAggregation(
            parcellation="Schaefer100x7",
            method="mean",
            time_method_params={"pick": [0]},
            on="VBM_GM",
        )

    with pytest.warns(RuntimeWarning, match="No time dimension to aggregate"):
        input = {
            "BOLD": {
                "data": fmri_img.slicer[..., 0:1],
                "meta": {},
                "space": "MNI",
            }
        }
        marker.fit_transform(input)
