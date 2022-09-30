"""Provide tests for HCP1200."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from junifer.datagrabber.hcp import DataladHCP1200
from junifer.utils import configure_logging


URI = "https://gin.g-node.org/juaml/datalad-example-hcp1200"


def test_dataladhcp1200_datagrabber() -> None:
    """Test datalad HCP1200 datagrabber."""
    configure_logging(level="DEBUG")
    dg = DataladHCP1200()
    # Set URI to Gin
    dg.uri = URI
    # Set correct root directory
    dg._rootdir = "."
    with dg:
        # Get all elements
        all_elements = dg.get_elements()
        # Get test element
        test_element = all_elements[0]
        # Get test element data
        out = dg[test_element]
        # Asserts data type
        assert "BOLD" in out
        # Assert data file name
        assert out["BOLD"]["path"].name == "rfMRI_REST1_LR_hp2000_clean.nii.gz"
        # Assert data file path exists
        assert out["BOLD"]["path"].exists()
        # Assert data file path is a file
        assert out["BOLD"]["path"].is_file()
        # Assert metadata
        assert "meta" in out
        meta = out["meta"]
        assert "element" in meta
        assert "subject" in meta["element"]
        assert test_element[0] == meta["element"]["subject"]
