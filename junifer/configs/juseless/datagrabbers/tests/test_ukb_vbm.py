"""Provide tests for JuselessDataladUKBVBM."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import socket

import pytest

from junifer.configs.juseless.datagrabbers import JuselessDataladUKBVBM
from junifer.utils.logging import configure_logging


# Check if the test is running on juseless
if socket.gethostname() != "juseless":
    pytest.skip("These tests are only for juseless", allow_module_level=True)

configure_logging(level="DEBUG")


def test_JuselessDataladUKBVBM() -> None:
    """Test JuselessDataladUKBVBM."""
    with JuselessDataladUKBVBM() as dg:
        all_elements = dg.get_elements()
        test_element = all_elements[0]
        out = dg[test_element]
        assert "VBM_GM" in out
        assert (
            out["VBM_GM"]["path"].name
            == f"m0wp1sub-{test_element[0]}_ses-{test_element[1]}_T1w.nii.gz"
        )
        assert out["VBM_GM"]["path"].exists()
