"""Provide tests for UCLA juseless datagrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import socket
from typing import Optional

import pytest

from junifer.configs.juseless.datagrabbers import JuselessUCLA
from junifer.utils.logging import configure_logging


# Check if the test is running on juseless
if socket.gethostname() != "juseless":
    pytest.skip("These tests are only for juseless", allow_module_level=True)

configure_logging(level="DEBUG")


def test_juseless_ucla_datagrabber() -> None:
    """Test juseless ucla datagrabber."""
    with JuselessUCLA() as dg:
        all_elements = dg.get_elements()
        test_element = all_elements[0]
        out = dg[test_element]

        types = [
            "BOLD",
            "BOLD_confounds",
            "T1w",
            "probseg_CSF",
            "probseg_GM",
            "probseg_WM",
        ]

        for t in types:
            assert t in out
            assert out[t]["path"].exists()


@pytest.mark.parametrize(
    "tasks",
    [None, "rest", ["rest", "stopsignal"]],
)
def test_juseless_ucla_datagrabber_task_params(tasks: Optional[str]) -> None:
    """Test juseless ucla datagrabber with different task parameters.

    Parameters
    ----------
    tasks : str
        The parametrized tasks in the UCLA dataset.

    """

    all_tasks = [
        "rest",
        "bart",
        "bht",
        "pamenc",
        "pamret",
        "scap",
        "taskswitch",
        "stopsignal",
    ]

    with JuselessUCLA(tasks=tasks) as dg:
        all_elements = dg.get_elements()

        if tasks is None:
            for el in all_elements:
                assert el[1] in all_tasks
        elif tasks == "rest":
            for el in all_elements:
                assert el[1] == "rest"
        else:
            for el in all_elements:
                assert el[1] in ["rest", "stopsignal"]


def test_juseless_ucla_datagrabber_invalid_tasks() -> None:
    """Test juseless ucla datagrabber with invalid task parameters."""
    with pytest.raises(
        ValueError, match="invalid is not a valid task in the UCLA"
    ):
        JuselessUCLA(tasks="invalid")
