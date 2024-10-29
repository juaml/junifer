"""Provide tests for sphere aggregation."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

import pytest
from nilearn.maskers import NiftiSpheresMasker
from numpy.testing import assert_array_equal

from junifer.data import CoordinatesRegistry, MaskRegistry
from junifer.datareader import DefaultDataReader
from junifer.markers.sphere_aggregation import SphereAggregation
from junifer.storage import SQLiteFeatureStorage
from junifer.testing.datagrabbers import (
    OasisVBMTestingDataGrabber,
    SPMAuditoryTestingDataGrabber,
)


# Define common variables
COORDS = "DMNBuckner"
RADIUS = 8


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
def test_SphereAggregation_input_output(
    input_type: str, storage_type: str
) -> None:
    """Test SphereAggregation input and output types.

    Parameters
    ----------
    input_type : str
        The parametrized input type.
    storage_type : str
        The parametrized storage type.

    """
    assert storage_type == SphereAggregation(
        coords="DMNBuckner",
        method="mean",
        on=input_type,
    ).get_output_type(input_type=input_type, output_feature="aggregation")


def test_SphereAggregation_3D() -> None:
    """Test SphereAggregation object on 3D images."""
    with OasisVBMTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        # Create SphereAggregation object
        marker = SphereAggregation(
            coords=COORDS, method="mean", radius=RADIUS, on="VBM_GM"
        )
        sphere_agg_vbm_gm_data = marker.fit_transform(element_data)["VBM_GM"][
            "aggregation"
        ]["data"]

        # Compare with nilearn
        # Load testing coordinates
        testing_coords, _ = CoordinatesRegistry().get(
            coords=COORDS, target_data=element_data["VBM_GM"]
        )
        # Extract data
        nifti_spheres_masker = NiftiSpheresMasker(
            seeds=testing_coords, radius=RADIUS
        )
        nifti_spheres_masked_vbm_gm = nifti_spheres_masker.fit_transform(
            element_data["VBM_GM"]["data"]
        )

        assert sphere_agg_vbm_gm_data.ndim == 2
        assert_array_equal(
            nifti_spheres_masked_vbm_gm.shape, sphere_agg_vbm_gm_data.shape
        )
        assert_array_equal(nifti_spheres_masked_vbm_gm, sphere_agg_vbm_gm_data)


def test_SphereAggregation_4D() -> None:
    """Test SphereAggregation object on 4D images."""
    with SPMAuditoryTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub001"])
        # Create SphereAggregation object
        marker = SphereAggregation(
            coords=COORDS, method="mean", radius=RADIUS, on="BOLD"
        )
        sphere_agg_bold_data = marker.fit_transform(element_data)["BOLD"][
            "aggregation"
        ]["data"]

        # Compare with nilearn
        # Load testing coordinates
        testing_coords, _ = CoordinatesRegistry().get(
            coords=COORDS, target_data=element_data["BOLD"]
        )
        # Extract data
        nifti_spheres_masker = NiftiSpheresMasker(
            seeds=testing_coords, radius=RADIUS
        )
        nifti_spheres_masked_bold = nifti_spheres_masker.fit_transform(
            element_data["BOLD"]["data"]
        )

        assert sphere_agg_bold_data.ndim == 2
        assert_array_equal(
            nifti_spheres_masked_bold.shape, sphere_agg_bold_data.shape
        )
        assert_array_equal(nifti_spheres_masked_bold, sphere_agg_bold_data)


def test_SphereAggregation_storage(tmp_path: Path) -> None:
    """Test SphereAggregation storage.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    # Store 3D
    with OasisVBMTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        storage = SQLiteFeatureStorage(
            uri=tmp_path / "test_sphere_storage_3D.sqlite", upsert="ignore"
        )
        marker = SphereAggregation(
            coords=COORDS, method="mean", radius=RADIUS, on="VBM_GM"
        )
        marker.fit_transform(input=element_data, storage=storage)
        features = storage.list_features()
        assert any(
            x["name"] == "VBM_GM_SphereAggregation_aggregation"
            for x in features.values()
        )

    # Store 4D
    with SPMAuditoryTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub001"])
        storage = SQLiteFeatureStorage(
            uri=tmp_path / "test_sphere_storage_4D.sqlite", upsert="ignore"
        )
        marker = SphereAggregation(
            coords=COORDS, method="mean", radius=RADIUS, on="BOLD"
        )
        marker.fit_transform(input=element_data, storage=storage)
        features = storage.list_features()
        assert any(
            x["name"] == "BOLD_SphereAggregation_aggregation"
            for x in features.values()
        )


def test_SphereAggregation_3D_mask() -> None:
    """Test SphereAggregation object on 3D images using mask."""
    with OasisVBMTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        # Create SphereAggregation object
        marker = SphereAggregation(
            coords=COORDS,
            method="mean",
            radius=RADIUS,
            on="VBM_GM",
            masks="compute_brain_mask",
        )
        sphere_agg_vbm_gm_data = marker.fit_transform(element_data)["VBM_GM"][
            "aggregation"
        ]["data"]

        # Compare with nilearn
        # Load testing coordinates
        testing_coords, _ = CoordinatesRegistry().get(
            coords=COORDS, target_data=element_data["VBM_GM"]
        )
        # Load mask
        mask_img = MaskRegistry().get(
            "compute_brain_mask", target_data=element_data["VBM_GM"]
        )
        # Extract data
        nifti_spheres_masker = NiftiSpheresMasker(
            seeds=testing_coords, radius=RADIUS, mask_img=mask_img
        )
        nifti_spheres_masked_vbm_agg = nifti_spheres_masker.fit_transform(
            element_data["VBM_GM"]["data"]
        )

        assert sphere_agg_vbm_gm_data.ndim == 2
        assert_array_equal(
            nifti_spheres_masked_vbm_agg.shape,
            nifti_spheres_masked_vbm_agg.shape,
        )
        assert_array_equal(
            nifti_spheres_masked_vbm_agg, nifti_spheres_masked_vbm_agg
        )


def test_SphereAggregation_4D_agg_time() -> None:
    """Test SphereAggregation object on 4D images, aggregating time."""
    with SPMAuditoryTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub001"])
        # Create SphereAggregation object
        marker = SphereAggregation(
            coords=COORDS,
            method="mean",
            radius=RADIUS,
            time_method="mean",
            on="BOLD",
        )
        sphere_agg_bold_data = marker.fit_transform(element_data)["BOLD"][
            "aggregation"
        ]["data"]

        # Compare with nilearn
        # Load testing coordinates
        testing_coords, _ = CoordinatesRegistry().get(
            coords=COORDS, target_data=element_data["BOLD"]
        )
        # Extract data
        nifti_spheres_masker = NiftiSpheresMasker(
            seeds=testing_coords, radius=RADIUS
        )
        nifti_spheres_masked_bold = nifti_spheres_masker.fit_transform(
            element_data["BOLD"]["data"]
        )
        nifti_spheres_masked_bold_mean = nifti_spheres_masked_bold.mean(axis=0)

        assert sphere_agg_bold_data.ndim == 1
        assert_array_equal(
            nifti_spheres_masked_bold_mean.shape, sphere_agg_bold_data.shape
        )
        assert_array_equal(
            nifti_spheres_masked_bold_mean, sphere_agg_bold_data
        )

        # Test picking first time point
        nifti_spheres_masked_bold_pick_0 = nifti_spheres_masked_bold[:1, :]
        marker = SphereAggregation(
            coords=COORDS,
            method="mean",
            radius=RADIUS,
            time_method="select",
            time_method_params={"pick": [0]},
            on="BOLD",
        )
        sphere_agg_bold_data = marker.fit_transform(element_data)["BOLD"][
            "aggregation"
        ]["data"]

        assert sphere_agg_bold_data.ndim == 2
        assert_array_equal(
            nifti_spheres_masked_bold_pick_0.shape, sphere_agg_bold_data.shape
        )
        assert_array_equal(
            nifti_spheres_masked_bold_pick_0, sphere_agg_bold_data
        )


def test_SphereAggregation_errors() -> None:
    """Test errors for SphereAggregation."""
    with pytest.raises(ValueError, match="can only be used with BOLD data"):
        SphereAggregation(
            coords=COORDS,
            method="mean",
            radius=RADIUS,
            time_method="pick",
            time_method_params={"pick": [0]},
            on="VBM_GM",
        )

    with pytest.raises(
        ValueError, match="can only be used with `time_method`"
    ):
        SphereAggregation(
            coords=COORDS,
            method="mean",
            radius=RADIUS,
            time_method_params={"pick": [0]},
            on="VBM_GM",
        )


def test_SphereAggregation_warning() -> None:
    """Test warning for SphereAggregation."""
    with SPMAuditoryTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub001"])
        with pytest.warns(
            RuntimeWarning, match="No time dimension to aggregate"
        ):
            marker = SphereAggregation(
                coords=COORDS,
                method="mean",
                radius=RADIUS,
                time_method="select",
                time_method_params={"pick": [0]},
                on="BOLD",
            )
            element_data["BOLD"]["data"] = element_data["BOLD"]["data"].slicer[
                ..., 0:1
            ]
            marker.fit_transform(element_data)
