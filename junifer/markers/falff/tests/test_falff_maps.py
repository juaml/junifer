"""Provide tests for ALFFMaps."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import logging
from pathlib import Path

import pytest
import scipy as sp

from junifer.datagrabber import PatternDataladDataGrabber
from junifer.datareader import DefaultDataReader
from junifer.markers import ALFFMaps
from junifer.pipeline import WorkDirManager
from junifer.pipeline.utils import _check_afni
from junifer.storage import HDF5FeatureStorage


MAPS = "Smith_rsn_10"


@pytest.mark.parametrize(
    "feature",
    [
        "alff",
        "falff",
    ],
)
def test_ALFFMaps_get_output_type(feature: str) -> None:
    """Test ALFFMaps get_output_type().

    Parameters
    ----------
    feature : str
        The parametrized feature name.

    """
    assert "vector" == ALFFMaps(
        maps=MAPS,
        using="junifer",
    ).get_output_type(input_type="BOLD", output_feature=feature)


def test_ALFFMaps(
    caplog: pytest.LogCaptureFixture,
    tmp_path: Path,
    maps_datagrabber: PatternDataladDataGrabber,
) -> None:
    """Test ALFFMaps.

    Parameters
    ----------
    caplog : pytest.LogCaptureFixture
        The pytest.LogCaptureFixture object.
    tmp_path : pathlib.Path
        The path to the test directory.
    maps_datagrabber : PatternDataladDataGrabber
        The testing PatternDataladDataGrabber, as fixture.

    """
    # Update workdir to current test's tmp_path
    WorkDirManager().workdir = tmp_path

    with caplog.at_level(logging.DEBUG):
        with maps_datagrabber as dg:
            element = dg[("sub-01", "sub-001", "rest", "1")]
            element_data = DefaultDataReader().fit_transform(element)

            # Initialize marker
            marker = ALFFMaps(
                maps=MAPS,
                using="junifer",
            )
            # Check correct output
            for name in ["alff", "falff"]:
                assert "vector" == marker.get_output_type(
                    input_type="BOLD", output_feature=name
                )

            # Fit transform marker on data
            output = marker.fit_transform(element_data)

            assert "Creating cache" in caplog.text

            # Get BOLD output
            assert "BOLD" in output
            for feature in output["BOLD"].keys():
                output_bold = output["BOLD"][feature]
                # Assert BOLD output keys
                assert "data" in output_bold
                assert "col_names" in output_bold

                output_bold_data = output_bold["data"]
                # Assert BOLD output data dimension
                assert output_bold_data.ndim == 2
                assert output_bold_data.shape == (1, 10)

            # Reset log capture
            caplog.clear()
            # Initialize storage
            storage = HDF5FeatureStorage(tmp_path / "falff_maps.hdf5")
            # Fit transform marker on data with storage
            marker.fit_transform(
                input=element_data,
                storage=storage,
            )
            # Check stored feature name
            features = storage.list_features()
            assert any(
                x["name"] in ["BOLD_ALFFMaps_alff", "BOLD_ALFFMaps_falff"]
                for x in features.values()
            )
            # Cache working correctly
            assert "Creating cache" not in caplog.text


@pytest.mark.skipif(
    _check_afni() is False, reason="requires AFNI to be in PATH"
)
def test_ALFFMaps_comparison(
    tmp_path: Path, maps_datagrabber: PatternDataladDataGrabber
) -> None:
    """Test ALFFMaps implementation comparison.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    maps_datagrabber : PatternDataladDataGrabber
        The testing PatternDataladDataGrabber, as fixture.

    """
    # Update workdir to current test's tmp_path
    WorkDirManager().workdir = tmp_path

    with maps_datagrabber as dg:
        element = dg[("sub-01", "sub-001", "rest", "1")]
        element_data = DefaultDataReader().fit_transform(element)

        # Initialize marker
        junifer_marker = ALFFMaps(
            maps=MAPS,
            using="junifer",
        )
        # Fit transform marker on data
        junifer_output = junifer_marker.fit_transform(element_data)
        # Get BOLD output
        junifer_output_bold = junifer_output["BOLD"]

        # Initialize marker
        afni_marker = ALFFMaps(
            maps=MAPS,
            using="afni",
        )
        # Fit transform marker on data
        afni_output = afni_marker.fit_transform(element_data)
        # Get BOLD output
        afni_output_bold = afni_output["BOLD"]

        for feature in afni_output_bold.keys():
            # Check for Pearson correlation coefficient
            r, _ = sp.stats.pearsonr(
                junifer_output_bold[feature]["data"][0],
                afni_output_bold[feature]["data"][0],
            )
            assert r > 0.97
