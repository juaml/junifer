"""Provide tests for ReHoParcels."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import logging
from pathlib import Path

import pytest
import scipy as sp

from junifer.datareader import DefaultDataReader
from junifer.markers import ReHoParcels
from junifer.pipeline import WorkDirManager
from junifer.pipeline.utils import _check_afni, _check_ants
from junifer.storage import SQLiteFeatureStorage
from junifer.testing.datagrabbers import (
    PartlyCloudyTestingDataGrabber,
    SPMAuditoryTestingDataGrabber,
)


def test_ReHoParcels(caplog: pytest.LogCaptureFixture, tmp_path: Path) -> None:
    """Test ReHoParcels.

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
            marker = ReHoParcels(
                parcellation="TianxS1x3TxMNInonlinear2009cAsym",
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
            storage = SQLiteFeatureStorage(tmp_path / "reho_parcels.sqlite")
            # Fit transform marker on data with storage
            marker.fit_transform(
                input=element_data,
                storage=storage,
            )
            # Cache working correctly
            assert "Creating cache" not in caplog.text


@pytest.mark.skipif(
    _check_ants() is False, reason="requires ANTs to be in PATH"
)
@pytest.mark.skipif(
    _check_afni() is False, reason="requires AFNI to be in PATH"
)
def test_ReHoParcels_comparison(tmp_path: Path) -> None:
    """Test ReHoParcels implementation comparison.

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
        junifer_marker = ReHoParcels(
            parcellation="Schaefer100x7", using="junifer"
        )
        # Fit transform marker on data
        junifer_output = junifer_marker.fit_transform(element_data)
        # Get BOLD output
        junifer_output_bold = junifer_output["BOLD"]["reho"]

        # Initialize marker
        afni_marker = ReHoParcels(parcellation="Schaefer100x7", using="afni")
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
