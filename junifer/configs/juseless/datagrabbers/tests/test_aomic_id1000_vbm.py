"""Provide tests for AOMICID1000 VBM juseless datagrabber."""

# Authors: Felix Hoffstaedter <f.hoffstaedter@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import socket

import pytest

from junifer.configs.juseless.datagrabbers import JuselessDataladAOMICID1000VBM
from junifer.utils.logging import configure_logging


# Check if the test is running on juseless
if socket.gethostname() != "juseless":
    pytest.skip("These tests are only for juseless", allow_module_level=True)

configure_logging(level="DEBUG")


def test_juselessdataladaomicid1000vbm_datagrabber() -> None:
    """Test datalad AOMICID1000VBM datagrabber."""
    with JuselessDataladAOMICID1000VBM() as dg:
        all_elements = dg.get_elements()
        test_element = all_elements[0]
        out = dg[test_element]
        assert "VBM_GM" in out
        assert (
            out["VBM_GM"]["path"].name
            == f"mwp1sub-{test_element}_run-2_T1w.nii.gz"
        )
        assert out["VBM_GM"]["path"].exists()
