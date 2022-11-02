"""Provide tests for Oasis VBM Testing datagrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from junifer.testing.datagrabbers import OasisVBMTestingDatagrabber


def test_OasisVBMTestingDatagrabber() -> None:
    """Test Oasis VBM Testing datagrabber."""
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
    with OasisVBMTestingDatagrabber() as dg:
        all_elements = dg.get_elements()
        assert set(all_elements) == set(expected_elements)
        out = dg["sub-01"]
        assert "VBM_GM" in out
        assert out["VBM_GM"]["path"].exists()
        assert out["VBM_GM"]["path"].is_file()
