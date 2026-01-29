"""Provide tests for JuselessUCLA."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import socket
from typing import Optional, Union

import pytest

from junifer.configs.juseless.datagrabbers import JuselessUCLA


# Check if the test is running on juseless
if socket.gethostname() != "juseless":
    pytest.skip("These tests are only for juseless", allow_module_level=True)


def test_JuselessUCLA() -> None:
    """Test JuselessUCLA."""
    with JuselessUCLA() as dg:
        all_elements = dg.get_elements()
        test_element = all_elements[0]
        out = dg[test_element]

        types = [
            "BOLD",
            "T1w",
            "VBM_CSF",
            "VBM_GM",
            "VBM_WM",
        ]

        for t in types:
            assert t in out
            assert out[t]["path"].exists()


@pytest.mark.parametrize(
    "types",
    [
        "BOLD",
        "T1w",
        "VBM_CSF",
        "VBM_GM",
        "VBM_WM",
        ["BOLD", "VBM_CSF"],
        ["T1w", "VBM_CSF"],
        ["VBM_GM", "VBM_WM"],
        ["BOLD", "T1w"],
    ],
)
def test_JuselessUCLA_partial_data_access(
    types: Union[str, list[str]],
) -> None:
    """Test JuselessUCLA DataGrabber partial data access.

    Parameters
    ----------
    types : str or list of str
        The parametrized types.

    """
    dg = JuselessUCLA(types=types)

    with dg:
        # Get all elements
        all_elements = dg.get_elements()
        # Get test element
        test_element = all_elements[0]
        # Get test element data
        out = dg[test_element]
        # Assert data type
        if isinstance(types, list):
            for type_ in types:
                assert type_ in out
        else:
            assert types in out


@pytest.mark.parametrize(
    "tasks",
    [None, "rest", ["rest", "stopsignal"]],
)
def test_JuselessUCLA_task_params(tasks: Optional[str]) -> None:
    """Test JuselessUCLA with different task parameters.

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
