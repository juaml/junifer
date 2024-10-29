"""Provide test for parcel aggregation."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import warnings
from pathlib import Path

import nibabel as nib
import numpy as np
import pytest
from nilearn.image import math_img, new_img_like
from nilearn.maskers import NiftiLabelsMasker, NiftiMasker
from nilearn.masking import compute_brain_mask
from numpy.testing import assert_array_almost_equal, assert_array_equal
from scipy.stats import trim_mean

from junifer.data import MaskRegistry, ParcellationRegistry
from junifer.datareader import DefaultDataReader
from junifer.markers.parcel_aggregation import ParcelAggregation
from junifer.storage import SQLiteFeatureStorage
from junifer.testing.datagrabbers import PartlyCloudyTestingDataGrabber


@pytest.mark.parametrize(
    "input_type, storage_type",
    [
        (
            "T1w",
            "vector",
        ),
        (
            "T2w",
            "vector",
        ),
        (
            "BOLD",
            "timeseries",
        ),
        (
            "VBM_GM",
            "vector",
        ),
        (
            "VBM_WM",
            "vector",
        ),
        (
            "VBM_CSF",
            "vector",
        ),
        (
            "fALFF",
            "vector",
        ),
        (
            "GCOR",
            "vector",
        ),
        (
            "LCOR",
            "vector",
        ),
    ],
)
def test_ParcelAggregation_input_output(
    input_type: str, storage_type: str
) -> None:
    """Test ParcelAggregation input and output types.

    Parameters
    ----------
    input_type : str
        The parametrized input type.
    storage_type : str
        The parametrized storage type.

    """
    assert storage_type == ParcelAggregation(
        parcellation="Schaefer100x7", method="mean", on=input_type
    ).get_output_type(input_type=input_type, output_feature="aggregation")


def test_ParcelAggregation_3D() -> None:
    """Test ParcelAggregation object on 3D images."""
    with PartlyCloudyTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        # Create ParcelAggregation object
        marker = ParcelAggregation(
            parcellation="TianxS1x3TxMNInonlinear2009cAsym",
            method="mean",
            on="BOLD",
        )
        element_data["BOLD"]["data"] = element_data["BOLD"]["data"].slicer[
            ..., 0:1
        ]

        # Compare with nilearn
        # Load testing parcellation
        testing_parcellation, _ = ParcellationRegistry().get(
            parcellations=["TianxS1x3TxMNInonlinear2009cAsym"],
            target_data=element_data["BOLD"],
        )
        # Binarize parcellation
        testing_parcellation_bin = math_img(
            "img != 0",
            img=testing_parcellation,
        )
        # Create NiftiMasker
        masker = NiftiMasker(
            testing_parcellation_bin,
            target_affine=element_data["BOLD"]["data"].affine,
        )
        data = masker.fit_transform(element_data["BOLD"]["data"])
        parcellation_values = np.squeeze(
            masker.transform(testing_parcellation)
        ).astype(int)
        # Compute the mean manually
        manual = []
        for t_v in sorted(np.unique(parcellation_values)):
            t_values = np.mean(data[:, parcellation_values == t_v])
            manual.append(t_values)
        manual = np.array(manual)[np.newaxis, :]

        # Create NiftiLabelsMasker
        nifti_labels_masker = NiftiLabelsMasker(
            labels_img=testing_parcellation
        )
        nifti_labels_masked_bold = nifti_labels_masker.fit_transform(
            element_data["BOLD"]["data"].slicer[..., 0:1]
        )

        parcel_agg_mean_bold_data = marker.fit_transform(element_data)["BOLD"][
            "aggregation"
        ]["data"]
        # Check that arrays are almost equal
        assert_array_equal(parcel_agg_mean_bold_data, manual)
        assert_array_almost_equal(nifti_labels_masked_bold, manual)

        # Check further
        assert parcel_agg_mean_bold_data.ndim == 2
        assert parcel_agg_mean_bold_data.shape[0] == 1
        assert_array_equal(
            nifti_labels_masked_bold.shape, parcel_agg_mean_bold_data.shape
        )
        assert_array_equal(nifti_labels_masked_bold, parcel_agg_mean_bold_data)

        # Compute std manually
        manual = []
        for t_v in sorted(np.unique(parcellation_values)):
            t_values = np.std(data[:, parcellation_values == t_v])
            manual.append(t_values)
        manual = np.array(manual)[np.newaxis, :]

        # Create ParcelAggregation object
        marker = ParcelAggregation(
            parcellation="TianxS1x3TxMNInonlinear2009cAsym",
            method="std",
            on="BOLD",
        )
        parcel_agg_std_bold_data = marker.fit_transform(element_data)["BOLD"][
            "aggregation"
        ]["data"]
        assert parcel_agg_std_bold_data.ndim == 2
        assert parcel_agg_std_bold_data.shape[0] == 1
        assert_array_equal(parcel_agg_std_bold_data, manual)

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

        # Create ParcelAggregation object
        marker = ParcelAggregation(
            parcellation="TianxS1x3TxMNInonlinear2009cAsym",
            method="trim_mean",
            method_params={"proportiontocut": 0.1},
            on="BOLD",
        )
        parcel_agg_trim_mean_bold_data = marker.fit_transform(element_data)[
            "BOLD"
        ]["aggregation"]["data"]
        assert parcel_agg_trim_mean_bold_data.ndim == 2
        assert parcel_agg_trim_mean_bold_data.shape[0] == 1
        assert_array_equal(parcel_agg_trim_mean_bold_data, manual)


def test_ParcelAggregation_4D():
    """Test ParcelAggregation object on 4D images."""
    with PartlyCloudyTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        # Create ParcelAggregation object
        marker = ParcelAggregation(
            parcellation="TianxS1x3TxMNInonlinear2009cAsym", method="mean"
        )
        parcel_agg_bold_data = marker.fit_transform(element_data)["BOLD"][
            "aggregation"
        ]["data"]

        # Compare with nilearn
        # Load testing parcellation
        testing_parcellation, _ = ParcellationRegistry().get(
            parcellations=["TianxS1x3TxMNInonlinear2009cAsym"],
            target_data=element_data["BOLD"],
        )
        # Extract data
        nifti_labels_masker = NiftiLabelsMasker(
            labels_img=testing_parcellation
        )
        nifti_labels_masked_bold = nifti_labels_masker.fit_transform(
            element_data["BOLD"]["data"]
        )

        assert parcel_agg_bold_data.ndim == 2
        assert_array_equal(
            nifti_labels_masked_bold.shape, parcel_agg_bold_data.shape
        )
        assert_array_equal(nifti_labels_masked_bold, parcel_agg_bold_data)


def test_ParcelAggregation_storage(tmp_path: Path) -> None:
    """Test ParcelAggregation storage.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    # Store 3D
    with PartlyCloudyTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        storage = SQLiteFeatureStorage(
            uri=tmp_path / "test_parcel_storage_3D.sqlite", upsert="ignore"
        )
        marker = ParcelAggregation(
            parcellation="TianxS1x3TxMNInonlinear2009cAsym",
            method="mean",
            on="BOLD",
        )
        element_data["BOLD"]["data"] = element_data["BOLD"]["data"].slicer[
            ..., 0:1
        ]
        marker.fit_transform(input=element_data, storage=storage)
        features = storage.list_features()
        assert any(
            x["name"] == "BOLD_ParcelAggregation_aggregation"
            for x in features.values()
        )

    # Store 4D
    with PartlyCloudyTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        storage = SQLiteFeatureStorage(
            uri=tmp_path / "test_parcel_storage_4D.sqlite", upsert="ignore"
        )
        marker = ParcelAggregation(
            parcellation="TianxS1x3TxMNInonlinear2009cAsym",
            method="mean",
            on="BOLD",
        )
        marker.fit_transform(input=element_data, storage=storage)
        features = storage.list_features()
        assert any(
            x["name"] == "BOLD_ParcelAggregation_aggregation"
            for x in features.values()
        )


def test_ParcelAggregation_3D_mask() -> None:
    """Test ParcelAggregation object on 3D images with mask."""
    with PartlyCloudyTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        # Create ParcelAggregation object
        marker = ParcelAggregation(
            parcellation="TianxS1x3TxMNInonlinear2009cAsym",
            method="mean",
            name="tian_mean",
            on="BOLD",
            masks="compute_brain_mask",
        )
        element_data["BOLD"]["data"] = element_data["BOLD"]["data"].slicer[
            ..., 0:1
        ]
        parcel_agg_bold_data = marker.fit_transform(element_data)["BOLD"][
            "aggregation"
        ]["data"]

        # Compare with nilearn
        # Load testing parcellation
        testing_parcellation, _ = ParcellationRegistry().get(
            parcellations=["TianxS1x3TxMNInonlinear2009cAsym"],
            target_data=element_data["BOLD"],
        )
        # Load mask
        mask_img = MaskRegistry().get(
            "compute_brain_mask", target_data=element_data["BOLD"]
        )
        # Extract data
        nifti_labels_masker = NiftiLabelsMasker(
            labels_img=testing_parcellation, mask_img=mask_img
        )
        nifti_labels_masked_bold = nifti_labels_masker.fit_transform(
            element_data["BOLD"]["data"].slicer[..., 0:1]
        )

        assert parcel_agg_bold_data.ndim == 2
        assert_array_equal(
            nifti_labels_masked_bold.shape, parcel_agg_bold_data.shape
        )
        assert_array_equal(nifti_labels_masked_bold, parcel_agg_bold_data)


def test_ParcelAggregation_3D_mask_computed() -> None:
    """Test ParcelAggregation object on 3D images with computed masks."""
    with PartlyCloudyTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        element_data["BOLD"]["data"] = element_data["BOLD"]["data"].slicer[
            ..., 0:1
        ]

        # Compare with nilearn
        # Load testing parcellation
        testing_parcellation, _ = ParcellationRegistry().get(
            parcellations=["TianxS1x3TxMNInonlinear2009cAsym"],
            target_data=element_data["BOLD"],
        )
        # Get a mask
        mask_img = compute_brain_mask(
            element_data["BOLD"]["data"], threshold=0.2
        )
        # Create NiftiLabelsMasker
        nifti_labels_masker = NiftiLabelsMasker(
            labels_img=testing_parcellation, mask_img=mask_img
        )
        nifti_labels_masked_bold_good = nifti_labels_masker.fit_transform(
            element_data["BOLD"]["data"]
        )

        # Get another mask
        mask_img = compute_brain_mask(
            element_data["BOLD"]["data"], threshold=0.5
        )
        # Create NiftiLabelsMasker
        nifti_labels_masker = NiftiLabelsMasker(
            labels_img=testing_parcellation, mask_img=mask_img
        )
        nifti_labels_masked_bold_bad = nifti_labels_masker.fit_transform(
            mask_img
        )

        # Use the ParcelAggregation object
        marker = ParcelAggregation(
            parcellation="TianxS1x3TxMNInonlinear2009cAsym",
            method="mean",
            masks={"compute_brain_mask": {"threshold": 0.2}},
            name="tian_mean",
            on="BOLD",
        )
        parcel_agg_mean_bold_data = marker.fit_transform(element_data)["BOLD"][
            "aggregation"
        ]["data"]

        assert parcel_agg_mean_bold_data.ndim == 2
        assert parcel_agg_mean_bold_data.shape[0] == 1
        assert_array_almost_equal(
            nifti_labels_masked_bold_good, parcel_agg_mean_bold_data
        )

        with pytest.raises(AssertionError):
            assert_array_almost_equal(
                parcel_agg_mean_bold_data, nifti_labels_masked_bold_bad
            )


def test_ParcelAggregation_3D_multiple_non_overlapping(tmp_path: Path) -> None:
    """Test ParcelAggregation with multiple non-overlapping parcellations.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with PartlyCloudyTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        element_data["BOLD"]["data"] = element_data["BOLD"]["data"].slicer[
            ..., 0:1
        ]

        # Load testing parcellation
        testing_parcellation, labels = ParcellationRegistry().get(
            parcellations=["TianxS1x3TxMNInonlinear2009cAsym"],
            target_data=element_data["BOLD"],
        )

        # Create two parcellations from it
        parcellation_data = testing_parcellation.get_fdata()
        parcellation1_data = parcellation_data.copy()
        parcellation1_data[parcellation1_data > 8] = 0
        parcellation2_data = parcellation_data.copy()
        parcellation2_data[parcellation2_data <= 8] = 0
        parcellation2_data[parcellation2_data > 0] -= 8
        labels1 = labels[:8]
        labels2 = labels[8:]

        parcellation1_img = new_img_like(
            testing_parcellation, parcellation1_data
        )
        parcellation2_img = new_img_like(
            testing_parcellation, parcellation2_data
        )

        parcellation1_path = tmp_path / "parcellation1.nii.gz"
        parcellation2_path = tmp_path / "parcellation2.nii.gz"

        nib.save(parcellation1_img, parcellation1_path)
        nib.save(parcellation2_img, parcellation2_path)

        ParcellationRegistry().register(
            name="TianxS1x3TxMNInonlinear2009cAsym_low",
            parcellation_path=parcellation1_path,
            parcels_labels=labels1,
            space="MNI152NLin2009cAsym",
            overwrite=True,
        )
        ParcellationRegistry().register(
            name="TianxS1x3TxMNInonlinear2009cAsym_high",
            parcellation_path=parcellation2_path,
            parcels_labels=labels2,
            space="MNI152NLin2009cAsym",
            overwrite=True,
        )

        # Use the ParcelAggregation object on the original parcellation
        marker_original = ParcelAggregation(
            parcellation="TianxS1x3TxMNInonlinear2009cAsym",
            method="mean",
            name="tian_mean",
            on="BOLD",
        )
        orig_mean = marker_original.fit_transform(element_data)["BOLD"][
            "aggregation"
        ]

        orig_mean_data = orig_mean["data"]
        assert orig_mean_data.ndim == 2
        assert orig_mean_data.shape == (1, 16)

        # Use the ParcelAggregation object on the two parcellations
        marker_split = ParcelAggregation(
            parcellation=[
                "TianxS1x3TxMNInonlinear2009cAsym_low",
                "TianxS1x3TxMNInonlinear2009cAsym_high",
            ],
            method="mean",
            name="tian_mean",
            on="BOLD",
        )

        # No warnings should be raised
        with warnings.catch_warnings():
            warnings.simplefilter("error", category=UserWarning)
            split_mean = marker_split.fit_transform(element_data)["BOLD"][
                "aggregation"
            ]

        split_mean_data = split_mean["data"]

        assert split_mean_data.ndim == 2
        assert split_mean_data.shape == (1, 16)

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
    with PartlyCloudyTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        element_data["BOLD"]["data"] = element_data["BOLD"]["data"].slicer[
            ..., 0:1
        ]

        # Load testing parcellation
        testing_parcellation, labels = ParcellationRegistry().get(
            parcellations=["TianxS1x3TxMNInonlinear2009cAsym"],
            target_data=element_data["BOLD"],
        )

        # Create two parcellations from it
        parcellation_data = testing_parcellation.get_fdata()
        parcellation1_data = parcellation_data.copy()
        parcellation1_data[parcellation1_data > 8] = 0
        parcellation2_data = parcellation_data.copy()

        # Make the second parcellation overlap with the first
        parcellation2_data[parcellation2_data <= 6] = 0
        parcellation2_data[parcellation2_data > 0] -= 6
        labels1 = [f"low_{x}" for x in labels[:8]]  # Change the labels
        labels2 = [f"high_{x}" for x in labels[6:]]  # Change the labels

        parcellation1_img = new_img_like(
            testing_parcellation, parcellation1_data
        )
        parcellation2_img = new_img_like(
            testing_parcellation, parcellation2_data
        )

        parcellation1_path = tmp_path / "parcellation1.nii.gz"
        parcellation2_path = tmp_path / "parcellation2.nii.gz"

        nib.save(parcellation1_img, parcellation1_path)
        nib.save(parcellation2_img, parcellation2_path)

        ParcellationRegistry().register(
            name="TianxS1x3TxMNInonlinear2009cAsym_low",
            parcellation_path=parcellation1_path,
            parcels_labels=labels1,
            space="MNI152NLin2009cAsym",
            overwrite=True,
        )
        ParcellationRegistry().register(
            name="TianxS1x3TxMNInonlinear2009cAsym_high",
            parcellation_path=parcellation2_path,
            parcels_labels=labels2,
            space="MNI152NLin2009cAsym",
            overwrite=True,
        )

        # Use the ParcelAggregation object on the original parcellation
        marker_original = ParcelAggregation(
            parcellation="TianxS1x3TxMNInonlinear2009cAsym",
            method="mean",
            name="tian_mean",
            on="BOLD",
        )
        orig_mean = marker_original.fit_transform(element_data)["BOLD"][
            "aggregation"
        ]

        orig_mean_data = orig_mean["data"]
        assert orig_mean_data.ndim == 2
        assert orig_mean_data.shape == (1, 16)

        # Use the ParcelAggregation object on the two parcellations
        marker_split = ParcelAggregation(
            parcellation=[
                "TianxS1x3TxMNInonlinear2009cAsym_low",
                "TianxS1x3TxMNInonlinear2009cAsym_high",
            ],
            method="mean",
            name="tian_mean",
            on="BOLD",
        )
        # Warning should be raised
        with pytest.warns(RuntimeWarning, match="overlapping voxels"):
            split_mean = marker_split.fit_transform(element_data)["BOLD"][
                "aggregation"
            ]

        split_mean_data = split_mean["data"]

        assert split_mean_data.ndim == 2
        assert split_mean_data.shape == (1, 18)

        # Overlapping voxels should be NaN
        assert np.isnan(split_mean_data[:, 8:10]).all()

        non_nan = split_mean_data[~np.isnan(split_mean_data)]
        # Data should be the same
        assert_array_equal(orig_mean_data, non_nan[None, :])

        # Labels should be "low" for the first 8 and "high" for the second 8
        assert all(x.startswith("low") for x in split_mean["col_names"][:8])
        assert all(x.startswith("high") for x in split_mean["col_names"][8:])


def test_ParcelAggregation_3D_multiple_duplicated_labels(
    tmp_path: Path,
) -> None:
    """Test ParcelAggregation with two parcellations with duplicated labels.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with PartlyCloudyTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        element_data["BOLD"]["data"] = element_data["BOLD"]["data"].slicer[
            ..., 0:1
        ]

        # Load testing parcellation
        testing_parcellation, labels = ParcellationRegistry().get(
            parcellations=["TianxS1x3TxMNInonlinear2009cAsym"],
            target_data=element_data["BOLD"],
        )

        # Create two parcellations from it
        parcellation_data = testing_parcellation.get_fdata()
        parcellation1_data = parcellation_data.copy()
        parcellation1_data[parcellation1_data > 8] = 0
        parcellation2_data = parcellation_data.copy()
        parcellation2_data[parcellation2_data <= 8] = 0
        parcellation2_data[parcellation2_data > 0] -= 8
        labels1 = labels[:8]
        labels2 = labels[7:-1]  # One label is duplicated

        parcellation1_img = new_img_like(
            testing_parcellation, parcellation1_data
        )
        parcellation2_img = new_img_like(
            testing_parcellation, parcellation2_data
        )

        parcellation1_path = tmp_path / "parcellation1.nii.gz"
        parcellation2_path = tmp_path / "parcellation2.nii.gz"

        nib.save(parcellation1_img, parcellation1_path)
        nib.save(parcellation2_img, parcellation2_path)

        ParcellationRegistry().register(
            name="TianxS1x3TxMNInonlinear2009cAsym_low",
            parcellation_path=parcellation1_path,
            parcels_labels=labels1,
            space="MNI152NLin2009cAsym",
            overwrite=True,
        )
        ParcellationRegistry().register(
            name="TianxS1x3TxMNInonlinear2009cAsym_high",
            parcellation_path=parcellation2_path,
            parcels_labels=labels2,
            space="MNI152NLin2009cAsym",
            overwrite=True,
        )

        # Use the ParcelAggregation object on the original parcellation
        marker_original = ParcelAggregation(
            parcellation="TianxS1x3TxMNInonlinear2009cAsym",
            method="mean",
            name="tian_mean",
            on="BOLD",
        )
        orig_mean = marker_original.fit_transform(element_data)["BOLD"][
            "aggregation"
        ]

        orig_mean_data = orig_mean["data"]
        assert orig_mean_data.ndim == 2
        assert orig_mean_data.shape == (1, 16)

        # Use the ParcelAggregation object on the two parcellations
        marker_split = ParcelAggregation(
            parcellation=[
                "TianxS1x3TxMNInonlinear2009cAsym_low",
                "TianxS1x3TxMNInonlinear2009cAsym_high",
            ],
            method="mean",
            name="tian_mean",
            on="BOLD",
        )

        # Warning should be raised
        with pytest.warns(RuntimeWarning, match="duplicated labels."):
            split_mean = marker_split.fit_transform(element_data)["BOLD"][
                "aggregation"
            ]

        split_mean_data = split_mean["data"]

        assert split_mean_data.ndim == 2
        assert split_mean_data.shape == (1, 16)

        # Data should be the same
        assert_array_equal(orig_mean_data, split_mean_data)

        # Labels should be prefixed with the parcellation name
        col_names = [
            f"TianxS1x3TxMNInonlinear2009cAsym_low_{x}" for x in labels1
        ]
        col_names += [
            f"TianxS1x3TxMNInonlinear2009cAsym_high_{x}" for x in labels2
        ]
        assert col_names == split_mean["col_names"]


def test_ParcelAggregation_4D_agg_time():
    """Test ParcelAggregation object on 4D images, aggregating time."""
    with PartlyCloudyTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        # Create ParcelAggregation object
        marker = ParcelAggregation(
            parcellation="TianxS1x3TxMNInonlinear2009cAsym",
            method="mean",
            time_method="mean",
            on="BOLD",
        )
        parcel_agg_bold_data = marker.fit_transform(element_data)["BOLD"][
            "aggregation"
        ]["data"]

        # Compare with nilearn
        # Loading testing parcellation
        testing_parcellation, _ = ParcellationRegistry().get(
            parcellations=["TianxS1x3TxMNInonlinear2009cAsym"],
            target_data=element_data["BOLD"],
        )
        # Extract data
        nifti_labels_masker = NiftiLabelsMasker(
            labels_img=testing_parcellation
        )
        nifti_labels_masked_bold = nifti_labels_masker.fit_transform(
            element_data["BOLD"]["data"]
        )
        nifti_labels_masked_bold_mean = nifti_labels_masked_bold.mean(axis=0)

        assert parcel_agg_bold_data.ndim == 1
        assert_array_equal(
            nifti_labels_masked_bold_mean.shape, parcel_agg_bold_data.shape
        )
        assert_array_almost_equal(
            nifti_labels_masked_bold_mean, parcel_agg_bold_data, decimal=2
        )

        # Test picking first time point
        nifti_labels_masked_bold_pick_0 = nifti_labels_masked_bold[:1, :]
        marker = ParcelAggregation(
            parcellation="TianxS1x3TxMNInonlinear2009cAsym",
            method="mean",
            time_method="select",
            time_method_params={"pick": [0]},
            on="BOLD",
        )
        parcel_agg_bold_data = marker.fit_transform(element_data)["BOLD"][
            "aggregation"
        ]["data"]

        assert parcel_agg_bold_data.ndim == 2
        assert_array_equal(
            nifti_labels_masked_bold_pick_0.shape, parcel_agg_bold_data.shape
        )
        assert_array_equal(
            nifti_labels_masked_bold_pick_0, parcel_agg_bold_data
        )


def test_ParcelAggregation_errors() -> None:
    """Test errors for ParcelAggregation."""
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


def test_ParcelAggregation_warning() -> None:
    """Test warning for ParcelAggregation."""
    with PartlyCloudyTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        with pytest.warns(
            RuntimeWarning, match="No time dimension to aggregate"
        ):
            marker = ParcelAggregation(
                parcellation="TianxS1x3TxMNInonlinear2009cAsym",
                method="mean",
                time_method="select",
                time_method_params={"pick": [0]},
                on="BOLD",
            )
            element_data["BOLD"]["data"] = element_data["BOLD"]["data"].slicer[
                ..., 0:1
            ]
            marker.fit_transform(element_data)
