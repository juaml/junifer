"""Provide tests for eNKI juseless datagrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Vera Komeyer <v.komeyer@fz-juelich.de>
#          Xuan Li <xu.li@fz-juelich.de>
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
    """Test eNKI datagrabber."""

    expected_types = [
        "T1w",
        "BOLD",
        "BOLD_confounds",
        "probseg_GM",
        "probseg_CSF",
        "probseg_WM",
    ]
    with JuselesseNKI() as dg:
        all_elements = dg.get_elements()
        test_element = all_elements[0]
        out = dg[test_element]
        for et in expected_types:
            assert et in out
            assert out[et]["path"].exists()


def test_juselessenki_datagrabber_invalid_session() -> None:
    """Test eNKI datagrabber with invalid session."""
    with pytest.raises(ValueError, match="Invalid eNKI datagrabber session."):
        with JuselesseNKI(sessions="notavalidsession"):
            pass


def test_juselessenki_datagrabber_invalid_TRs() -> None:
    """Test if the allowed TRs exists."""

    with JuselesseNKI() as dg:
        all_elements = dg.get_elements()
        assert([i for i, v in enumerate(all_elements) if v[3] == '645'])
        assert([i for i, v in enumerate(all_elements) if v[3] == '1400'])
        assert([i for i, v in enumerate(all_elements) if v[3] == 'cap'])
        