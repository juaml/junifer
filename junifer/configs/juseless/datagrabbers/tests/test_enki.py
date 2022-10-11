"""Provide tests for IXI VBM juseless datagrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import socket

import pytest

from junifer.configs.juseless.datagrabbers import JuselesseNKI
from junifer.utils.logging import configure_logging

# Check if the test is running on juseless
if socket.gethostname() != "juseless":
    pytest.skip("These tests are only for juseless", allow_module_level=True)

configure_logging(level="DEBUG")


def test_juselessenki_datagrabber() -> None:
    """Test datalad eNKI datagrabber."""

    expected_types = ["T1w", "BOLD", "BOLD_confounds"]
    with JuselesseNKI() as dg:
        all_elements = dg.get_elements()
        test_element = all_elements[0]
        out = dg[test_element]
        for et in expected_types:
            assert et in out

        # element is
        # subject, session, task, TR)
        assert out["BOLD"]["path"].name == (
            f"sub-{test_element[0]}_ses-{test_element[1]}_task-"
            f"{test_element[2]}_acq-{test_element[3]}_space-MNI152NLin6Asym_"
            "desc-preproc_bold.nii.gz"
        )
        assert out["BOLD"]["path"].exists()


def test_juselessenki_datagrabber_invalid_session() -> None:
    """Test eNKI datagrabber with invalid session."""
    with pytest.raises(ValueError, match="notavalidsite"):
        with JuselesseNKI(sessions="notavalidsite"):
            pass
