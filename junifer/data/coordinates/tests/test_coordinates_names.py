"""Provide tests for coordinates VOI names sanitizing."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

import pytest

from junifer.data.coordinates._coordinates import _sanitize_names


@pytest.mark.parametrize(
    "names, expected",
    [
        (["a", "b", "c"], ["a", "b", "c"]),
        (["inf cerebellum", "vmPFC"], ["inf_cerebellum", "vmPFC"]),
        (["a", "b", "a", "c", "a"], ["a-1", "b", "a-2", "c", "a-3"]),
        (
            ["mid insula", "mid insula", "x"],
            ["mid_insula-1", "mid_insula-2", "x"],
        ),
        ([1, 2, 3], [1, 2, 3]),
        (["a", "a", "a-1"], ["a-2", "a-3", "a-1"]),
        (["a-1", "a", "a"], ["a-1", "a-2", "a-3"]),
    ],
)
def test_sanitize_names(names: list, expected: list) -> None:
    """Test _sanitize_names.

    Parameters
    ----------
    names : list
        The parametrized VOI names.
    expected : list
        The parametrized expected sanitized names.

    """
    assert _sanitize_names(names) == expected
