"""Provide tests for ALFFSpheres."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import logging
from pathlib import Path

import pytest
import scipy as sp

from junifer.datareader import DefaultDataReader
from junifer.markers.falff import ALFFSpheres
from junifer.pipeline import WorkDirManager
from junifer.pipeline.utils import _check_afni
from junifer.storage import SQLiteFeatureStorage
from junifer.testing.datagrabbers import PartlyCloudyTestingDataGrabber


COORDINATES = "DMNBuckner"


@pytest.mark.parametrize(
    "feature",
    [
        "alff",
        "falff",
    ],
)
def test_ALFFSpheres_get_output_type(feature: str) -> None:
    """Test ALFFSpheres get_output_type().

    Parameters
    ----------
    feature : str
        The parametrized feature name.

    """
    assert "vector" == ALFFSpheres(
        coords=COORDINATES,
        using="junifer",
    ).get_output_type(input_type="BOLD", output_feature=feature)


def test_ALFFSpheres(caplog: pytest.LogCaptureFixture, tmp_path: Path) -> None:
    """Test ALFFSpheres.

    Parameters
    ----------
    caplog : pytest.LogCaptureFixture
        The pytest.LogCaptureFixture object.
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with caplog.at_level(logging.DEBUG):
        with PartlyCloudyTestingDataGrabber() as dg:
            element_data = DefaultDataReader().fit_transform(dg["sub-01"])
            # Update workdir to current test's tmp_path
            WorkDirManager().workdir = tmp_path

            # Initialize marker
            marker = ALFFSpheres(
                coords=COORDINATES,
                using="junifer",
                radius=5.0,
            )
            # Fit transform marker on data
            output = marker.fit_transform(element_data)

            # Tests for ALFFParcels run before this with the same data and that
            # should create the cache
            assert "Calculating ALFF and fALFF" in caplog.text

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
                assert output_bold_data.shape == (1, 6)

            # Reset log capture
            caplog.clear()
            # Initialize storage
            storage = SQLiteFeatureStorage(tmp_path / "falff_spheres.sqlite")
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
def test_ALFFSpheres_comparison(tmp_path: Path) -> None:
    """Test ALFFSpheres implementation comparison.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with PartlyCloudyTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        # Update workdir to current test's tmp_path
        WorkDirManager().workdir = tmp_path

        # Initialize marker
        junifer_marker = ALFFSpheres(
            coords=COORDINATES,
            using="junifer",
            radius=5.0,
        )
        # Fit transform marker on data
        junifer_output = junifer_marker.fit_transform(element_data)
        # Get BOLD output
        junifer_output_bold = junifer_output["BOLD"]

        # Initialize marker
        afni_marker = ALFFSpheres(
            coords=COORDINATES,
            using="afni",
            radius=5.0,
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
            assert r > 0.99
