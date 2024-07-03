"""Provide tests for ReHoSpheres."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import logging
from pathlib import Path

import pytest
import scipy as sp

from junifer.datareader import DefaultDataReader
from junifer.markers import ReHoSpheres
from junifer.pipeline import WorkDirManager
from junifer.pipeline.utils import _check_afni
from junifer.storage import SQLiteFeatureStorage
from junifer.testing.datagrabbers import SPMAuditoryTestingDataGrabber


COORDINATES = "DMNBuckner"


def test_ReHoSpheres(caplog: pytest.LogCaptureFixture, tmp_path: Path) -> None:
    """Test ReHoSpheres.

    Parameters
    ----------
    caplog : pytest.LogCaptureFixture
        The pytest.LogCaptureFixture object.
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with caplog.at_level(logging.DEBUG):
        with SPMAuditoryTestingDataGrabber() as dg:
            element_data = DefaultDataReader().fit_transform(dg["sub001"])
            # Update workdir to current test's tmp_path
            WorkDirManager().workdir = tmp_path
            # Initialize marker
            marker = ReHoSpheres(
                coords=COORDINATES, using="junifer", radius=10.0
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
            storage = SQLiteFeatureStorage(tmp_path / "reho_spheres.sqlite")
            # Fit transform marker on data with storage
            marker.fit_transform(
                input=element_data,
                storage=storage,
            )
            # Cache working correctly
            assert "Creating cache" not in caplog.text


@pytest.mark.skipif(
    _check_afni() is False, reason="requires AFNI to be in PATH"
)
def test_ReHoSpheres_comparison(tmp_path: Path) -> None:
    """Test ReHoSpheres implementation comparison.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with SPMAuditoryTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub001"])
        # Update workdir to current test's tmp_path
        WorkDirManager().workdir = tmp_path

        # Initialize marker
        junifer_marker = ReHoSpheres(
            coords=COORDINATES,
            using="junifer",
            radius=10.0,
        )
        # Fit transform marker on data
        junifer_output = junifer_marker.fit_transform(element_data)
        # Get BOLD output
        junifer_output_bold = junifer_output["BOLD"]["reho"]

        # Initialize marker
        afni_marker = ReHoSpheres(
            coords=COORDINATES,
            using="afni",
            radius=10.0,
        )
        # Fit transform marker on data
        afni_output = afni_marker.fit_transform(element_data)
        # Get BOLD output
        afni_output_bold = afni_output["BOLD"]["reho"]

        # Check for Pearson correlation coefficient
        r, _ = sp.stats.pearsonr(
            junifer_output_bold["data"].flatten(),
            afni_output_bold["data"].flatten(),
        )
        assert r >= 0.8  # 0.8 is a loose threshold
