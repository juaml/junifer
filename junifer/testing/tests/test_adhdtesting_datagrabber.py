"""Provide tests for ADHDTestingDataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from junifer.testing.datagrabbers import ADHDTestingDataGrabber


def test_ADHDTestingDataGrabber() -> None:
    """Test ADHDTestingDataGrabber."""
    expected_elements = [f"sub-{x:02d}" for x in range(1, 11)]
    with ADHDTestingDataGrabber() as dg:
        all_elements = dg.get_elements()
        assert set(all_elements) == set(expected_elements)
        out = dg["sub-01"]
        assert "BOLD" in out
        assert out["BOLD"]["path"].exists()
        assert out["BOLD"]["path"].is_file()
        assert out["BOLD"]["space"] == "MNI152NLin6Asym"
