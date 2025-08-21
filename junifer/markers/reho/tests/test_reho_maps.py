"""Provide tests for ReHoMaps."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import logging
from pathlib import Path

import pytest
import scipy as sp

from junifer.datagrabber import PatternDataladDataGrabber
from junifer.datareader import DefaultDataReader
from junifer.markers import ReHoMaps
from junifer.pipeline import WorkDirManager
from junifer.pipeline.utils import _check_afni
from junifer.storage import HDF5FeatureStorage


def test_ReHoMaps(
    caplog: pytest.LogCaptureFixture,
    tmp_path: Path,
    maps_datagrabber: PatternDataladDataGrabber,
) -> None:
    """Test ReHoMaps.

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
            marker = ReHoMaps(
                maps="Smith_rsn_10",
                using="junifer",
            )
            # Check correct output
            assert "vector" == marker.get_output_type(
                input_type="BOLD", output_feature="reho"
            )

            # Fit transform marker on data
            output = marker.fit_transform(element_data)

            assert "Creating cache" in caplog.text

            # Get BOLD output
            assert "BOLD" in output
            output_bold = output["BOLD"]["reho"]
            # Assert BOLD output keys
            assert "data" in output_bold
            assert "col_names" in output_bold

            output_bold_data = output_bold["data"]
            # Assert BOLD output data dimension
            assert output_bold_data.ndim == 2
            # Assert BOLD output data is normalized
            assert (output_bold_data > 0).all() and (
                output_bold_data < 1
            ).all()

            # Reset log capture
            caplog.clear()
            # Initialize storage
            storage = HDF5FeatureStorage(tmp_path / "reho_maps.hdf5")
            # Fit transform marker on data with storage
            marker.fit_transform(
                input=element_data,
                storage=storage,
            )
            # Check stored feature name
            features = storage.list_features()
            assert any(
                x["name"] == "BOLD_ReHoMaps_reho" for x in features.values()
            )
            # Cache working correctly
            assert "Creating cache" not in caplog.text


@pytest.mark.skipif(
    _check_afni() is False, reason="requires AFNI to be in PATH"
)
def test_ReHoMaps_comparison(
    tmp_path: Path, maps_datagrabber: PatternDataladDataGrabber
) -> None:
    """Test ReHoMaps implementation comparison.

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
        junifer_marker = ReHoMaps(maps="Smith_rsn_10", using="junifer")
        # Fit transform marker on data
        junifer_output = junifer_marker.fit_transform(element_data)
        # Get BOLD output
        junifer_output_bold = junifer_output["BOLD"]["reho"]

        # Initialize marker
        afni_marker = ReHoMaps(maps="Smith_rsn_10", using="afni")
        # Fit transform marker on data
        afni_output = afni_marker.fit_transform(element_data)
        # Get BOLD output
        afni_output_bold = afni_output["BOLD"]["reho"]

        # Check for Pearson correlation coefficient
        r, _ = sp.stats.pearsonr(
            junifer_output_bold["data"].flatten(),
            afni_output_bold["data"].flatten(),
        )
        assert r >= 0.2  # this is very bad, but they differ...
