"""Provide tests for SPMAuditoryTestingDataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

import nibabel as nib
import pytest

from junifer.testing.datagrabbers import SPMAuditoryTestingDataGrabber


pytestmark = pytest.mark.external


def test_SPMAuditoryTestingDataGrabber() -> None:
    """Test SPMAuditoryTestingDataGrabber."""
    expected_elements = [
        "sub001",
        "sub002",
        "sub003",
        "sub004",
        "sub005",
        "sub006",
        "sub007",
        "sub008",
        "sub009",
        "sub010",
    ]
    with SPMAuditoryTestingDataGrabber() as dg:
        all_elements = dg.get_elements()
        assert set(all_elements) == set(expected_elements)
        out = dg["sub001"]
        assert "BOLD" in out
        assert out["BOLD"]["path"].exists()
        assert out["BOLD"]["path"].is_file()

        assert "T1w" in out
        assert out["T1w"]["path"].exists()
        assert out["T1w"]["path"].is_file()


def test_SPMAuditoryTestingDataGrabber_n_timepoints() -> None:
    """Test SPMAuditoryTestingDataGrabber with fewer timepoints."""
    with SPMAuditoryTestingDataGrabber(n_timepoints=10) as dg:
        out = dg["sub001"]
        assert nib.load(out["BOLD"]["path"]).shape == (64, 64, 64, 10)
