"""Provide tests for PartlyCloudy datagrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from junifer.testing.datagrabbers import PartlyCloudyTestingDataGrabber


def test_PartlyCloudyTestingDataGrabber() -> None:
    """Test PartlyCloudy datagrabber."""
    expected_elements = [
        "sub-01",
        "sub-02",
        "sub-03",
        "sub-04",
        "sub-05",
        "sub-06",
        "sub-07",
        "sub-08",
        "sub-09",
        "sub-10",
    ]
    with PartlyCloudyTestingDataGrabber() as dg:
        all_elements = dg.get_elements()
        assert set(all_elements) == set(expected_elements)
        out = dg["sub-01"]
        assert "BOLD" in out
        assert out["BOLD"]["path"].exists()
        assert out["BOLD"]["path"].is_file()

        assert "BOLD_confounds" in out
        assert out["BOLD_confounds"]["path"].exists()
        assert out["BOLD_confounds"]["path"].is_file()
        assert "format" in out["BOLD_confounds"]
        assert "fmriprep" == out["BOLD_confounds"]["format"]

    with PartlyCloudyTestingDataGrabber(reduce_confounds=False) as dg:
        out = dg["sub-01"]
        assert "format" in out["BOLD_confounds"]
        assert "fmriprep" == out["BOLD_confounds"]["format"]
