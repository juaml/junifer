"""Provide test for maps aggregation."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from copy import deepcopy
from pathlib import Path

import pytest
from nilearn.maskers import NiftiMapsMasker
from numpy.testing import assert_array_almost_equal, assert_array_equal

from junifer.data import MapsRegistry, MaskRegistry
from junifer.data.masks import compute_brain_mask
from junifer.datagrabber import PatternDataladDataGrabber
from junifer.datareader import DefaultDataReader
from junifer.markers import MapsAggregation
from junifer.storage import HDF5FeatureStorage


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
def test_MapsAggregation_input_output(
    input_type: str, storage_type: str
) -> None:
    """Test MapsAggregation input and output types.

    Parameters
    ----------
    input_type : str
        The parametrized input type.
    storage_type : str
        The parametrized storage type.

    """
    assert storage_type == MapsAggregation(
        maps="Smith_rsn_10", on=input_type
    ).get_output_type(input_type=input_type, output_feature="aggregation")


def test_MapsAggregation_3D(
    maps_datagrabber: PatternDataladDataGrabber,
) -> None:
    """Test MapsAggregation on 3D data.

    Parameters
    ----------
    maps_datagrabber : PatternDataladDataGrabber
        The testing PatternDataladDataGrabber, as fixture.

    """
    with maps_datagrabber as dg:
        element = dg[("sub-01", "sub-001", "rest", "1")]
        element_data = DefaultDataReader().fit_transform(element)
        # Deepcopy data for later use
        input_data = deepcopy(element_data)
        # Modify for junifer
        element_data["BOLD"]["data"] = element_data["BOLD"]["data"].slicer[
            ...,
            0:1,
        ]
        marker = MapsAggregation(maps="Smith_rsn_10")
        maps_agg_bold_data = marker.fit_transform(element_data)["BOLD"][
            "aggregation"
        ]["data"]
        assert maps_agg_bold_data.ndim == 2

        # Compare with nilearn
        # Load testing maps
        maps, _ = MapsRegistry().get(
            maps="Smith_rsn_10",
            target_data=element_data["BOLD"],
        )
        # Extract data
        masker = NiftiMapsMasker(maps_img=maps)
        nifti_maps_masked_bold = masker.fit_transform(
            input_data["BOLD"]["data"].slicer[..., 0:1]
        )

        assert_array_equal(
            nifti_maps_masked_bold.shape, maps_agg_bold_data.shape
        )
        assert_array_equal(nifti_maps_masked_bold, maps_agg_bold_data)


def test_MapsAggregation_4D(
    maps_datagrabber: PatternDataladDataGrabber,
) -> None:
    """Test MapsAggregation on 4D data.

    Parameters
    ----------
    maps_datagrabber : PatternDataladDataGrabber
        The testing PatternDataladDataGrabber, as fixture.

    """
    with maps_datagrabber as dg:
        element = dg[("sub-01", "sub-001", "rest", "1")]
        element_data = DefaultDataReader().fit_transform(element)
        # Deepcopy data for later use
        input_data = deepcopy(element_data)
        marker = MapsAggregation(maps="Smith_rsn_10")
        maps_agg_bold_data = marker.fit_transform(element_data)["BOLD"][
            "aggregation"
        ]["data"]
        assert maps_agg_bold_data.ndim == 2

        # Compare with nilearn
        # Load testing maps
        maps, _ = MapsRegistry().get(
            maps="Smith_rsn_10",
            target_data=element_data["BOLD"],
        )
        # Extract data
        masker = NiftiMapsMasker(maps_img=maps)
        nifti_maps_masked_bold = masker.fit_transform(
            input_data["BOLD"]["data"]
        )

        assert_array_equal(
            nifti_maps_masked_bold.shape, maps_agg_bold_data.shape
        )
        assert_array_equal(nifti_maps_masked_bold, maps_agg_bold_data)


def test_MapsAggregation_storage(
    maps_datagrabber: PatternDataladDataGrabber, tmp_path: Path
) -> None:
    """Test MapsAggregation storage.

    Parameters
    ----------
    maps_datagrabber : PatternDataladDataGrabber
        The testing PatternDataladDataGrabber, as fixture.
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    # Store 3D
    with maps_datagrabber as dg:
        element = dg[("sub-01", "sub-001", "rest", "1")]
        element_data = DefaultDataReader().fit_transform(element)
        storage = HDF5FeatureStorage(
            uri=tmp_path / "test_maps_storage_3D.hdf5"
        )
        marker = MapsAggregation(
            maps="Smith_rsn_10",
            on="BOLD",
        )
        element_data["BOLD"]["data"] = element_data["BOLD"]["data"].slicer[
            ..., 0:1
        ]
        marker.fit_transform(input=element_data, storage=storage)
        features = storage.list_features()
        assert any(
            x["name"] == "BOLD_MapsAggregation_aggregation"
            for x in features.values()
        )

    # Store 4D
    with maps_datagrabber as dg:
        element = dg[("sub-01", "sub-001", "rest", "1")]
        element_data = DefaultDataReader().fit_transform(element)
        storage = HDF5FeatureStorage(
            uri=tmp_path / "test_maps_storage_4D.sqlite"
        )
        marker = MapsAggregation(
            maps="Smith_rsn_10",
            on="BOLD",
        )
        marker.fit_transform(input=element_data, storage=storage)
        features = storage.list_features()
        assert any(
            x["name"] == "BOLD_MapsAggregation_aggregation"
            for x in features.values()
        )


def test_MapsAggregation_3D_mask(
    maps_datagrabber: PatternDataladDataGrabber,
) -> None:
    """Test MapsAggregation on 3D data with mask.

    Parameters
    ----------
    maps_datagrabber : PatternDataladDataGrabber
        The testing PatternDataladDataGrabber, as fixture.

    """
    with maps_datagrabber as dg:
        element = dg[("sub-01", "sub-001", "rest", "1")]
        element_data = DefaultDataReader().fit_transform(element)
        # Deepcopy data for later use
        input_data = deepcopy(element_data)
        # Modify for junifer
        element_data["BOLD"]["data"] = element_data["BOLD"]["data"].slicer[
            ...,
            0:1,
        ]
        marker = MapsAggregation(
            maps="Smith_rsn_10",
            on="BOLD",
            masks="compute_brain_mask",
        )
        maps_agg_bold_data = marker.fit_transform(element_data)["BOLD"][
            "aggregation"
        ]["data"]
        assert maps_agg_bold_data.ndim == 2

        # Compare with nilearn
        # Load testing maps
        maps, _ = MapsRegistry().get(
            maps="Smith_rsn_10",
            target_data=element_data["BOLD"],
        )
        # Load mask
        mask_img = MaskRegistry().get(
            "compute_brain_mask", target_data=element_data["BOLD"]
        )
        # Extract data
        masker = NiftiMapsMasker(maps_img=maps, mask_img=mask_img)
        nifti_maps_masked_bold = masker.fit_transform(
            input_data["BOLD"]["data"].slicer[..., 0:1]
        )

        assert_array_equal(
            nifti_maps_masked_bold.shape, maps_agg_bold_data.shape
        )
        assert_array_equal(nifti_maps_masked_bold, maps_agg_bold_data)


def test_MapsAggregation_3D_mask_computed(
    maps_datagrabber: PatternDataladDataGrabber,
) -> None:
    """Test MapsAggregation on 3D data with computed masks.

    Parameters
    ----------
    maps_datagrabber : PatternDataladDataGrabber
        The testing PatternDataladDataGrabber, as fixture.

    """
    with maps_datagrabber as dg:
        element = dg[("sub-01", "sub-001", "rest", "1")]
        element_data = DefaultDataReader().fit_transform(element)

        # Compare with nilearn
        # Load testing maps
        maps, _ = MapsRegistry().get(
            maps="Smith_rsn_10",
            target_data=element_data["BOLD"],
        )
        # Get a mask
        mask_img = compute_brain_mask(element_data["BOLD"], threshold=0.2)
        # Create NiftiMapsMasker
        masker = NiftiMapsMasker(maps_img=maps, mask_img=mask_img)
        nifti_maps_masked_bold_good = masker.fit_transform(
            element_data["BOLD"]["data"]
        )

        # Get another mask
        mask_img = compute_brain_mask(element_data["BOLD"], threshold=0.5)
        # Create NiftiMapsMasker
        masker = NiftiMapsMasker(maps_img=maps, mask_img=mask_img)
        nifti_maps_masked_bold_bad = masker.fit_transform(mask_img)

        # Use the MapsAggregation object
        marker = MapsAggregation(
            maps="Smith_rsn_10",
            masks={"compute_brain_mask": {"threshold": 0.2}},
            on="BOLD",
        )
        maps_agg_bold_data = marker.fit_transform(element_data)["BOLD"][
            "aggregation"
        ]["data"]

        assert maps_agg_bold_data.ndim == 2
        assert_array_almost_equal(
            nifti_maps_masked_bold_good, maps_agg_bold_data
        )

        with pytest.raises(AssertionError):
            assert_array_almost_equal(
                maps_agg_bold_data, nifti_maps_masked_bold_bad
            )


def test_MapsAggregation_4D_agg_time(
    maps_datagrabber: PatternDataladDataGrabber,
):
    """Test MapsAggregation on 4D data, aggregating time.

    Parameters
    ----------
    maps_datagrabber : PatternDataladDataGrabber
        The testing PatternDataladDataGrabber, as fixture.

    """
    with maps_datagrabber as dg:
        element = dg[("sub-01", "sub-001", "rest", "1")]
        element_data = DefaultDataReader().fit_transform(element)
        # Create MapsAggregation object
        marker = MapsAggregation(
            maps="Smith_rsn_10",
            time_method="mean",
            on="BOLD",
        )
        maps_agg_bold_data = marker.fit_transform(element_data)["BOLD"][
            "aggregation"
        ]["data"]

        # Compare with nilearn
        # Loading testing maps
        maps, _ = MapsRegistry().get(
            maps="Smith_rsn_10",
            target_data=element_data["BOLD"],
        )
        # Extract data
        masker = NiftiMapsMasker(maps_img=maps)
        nifti_maps_masked_bold = masker.fit_transform(
            element_data["BOLD"]["data"]
        )
        nifti_maps_masked_bold_mean = nifti_maps_masked_bold.mean(axis=0)

        assert maps_agg_bold_data.ndim == 1
        assert_array_equal(
            nifti_maps_masked_bold_mean.shape, maps_agg_bold_data.shape
        )
        assert_array_almost_equal(
            nifti_maps_masked_bold_mean, maps_agg_bold_data, decimal=2
        )

        # Test picking first time point
        nifti_maps_masked_bold_pick_0 = nifti_maps_masked_bold[:1, :]
        marker = MapsAggregation(
            maps="Smith_rsn_10",
            time_method="select",
            time_method_params={"pick": [0]},
            on="BOLD",
        )
        maps_agg_bold_data = marker.fit_transform(element_data)["BOLD"][
            "aggregation"
        ]["data"]

        assert maps_agg_bold_data.ndim == 2
        assert_array_equal(
            nifti_maps_masked_bold_pick_0.shape, maps_agg_bold_data.shape
        )
        assert_array_equal(nifti_maps_masked_bold_pick_0, maps_agg_bold_data)


def test_MapsAggregation_errors() -> None:
    """Test errors for MapsAggregation."""
    with pytest.raises(ValueError, match="can only be used with BOLD data"):
        MapsAggregation(
            maps="Smith_rsn_10",
            time_method="select",
            time_method_params={"pick": [0]},
            on="VBM_GM",
        )

    with pytest.raises(
        ValueError, match="can only be used with `time_method`"
    ):
        MapsAggregation(
            maps="Smith_rsn_10",
            time_method_params={"pick": [0]},
            on="VBM_GM",
        )


def test_MapsAggregation_warning(
    maps_datagrabber: PatternDataladDataGrabber,
) -> None:
    """Test warning for MapsAggregation."""
    with maps_datagrabber as dg:
        element = dg[("sub-01", "sub-001", "rest", "1")]
        element_data = DefaultDataReader().fit_transform(element)
        with pytest.warns(
            RuntimeWarning, match="No time dimension to aggregate"
        ):
            marker = MapsAggregation(
                maps="Smith_rsn_10",
                time_method="select",
                time_method_params={"pick": [0]},
                on="BOLD",
            )
            element_data["BOLD"]["data"] = element_data["BOLD"]["data"].slicer[
                ..., 0:1
            ]
            marker.fit_transform(element_data)
