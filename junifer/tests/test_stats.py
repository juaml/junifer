"""Provide tests for stats."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Dict, Optional

import numpy as np
import pytest

from junifer.stats import get_aggfunc_by_name, kendall_w, winsorized_mean


@pytest.mark.parametrize(
    "name, params",
    [
        ("winsorized_mean", {"limits": [0.2, 0.7]}),
        ("mean", None),
        ("std", None),
        ("trim_mean", None),
        ("trim_mean", {"proportiontocut": 0.1}),
        ("kendall_w", None),
    ],
)
def test_get_aggfunc_by_name(name: str, params: Optional[Dict]) -> None:
    """Test aggregation function retrieval by name.

    Parameters
    ----------
    name : str
        The paramterized name of the method name.
    params : dict
        The parametrized parameters passed to the method.

    """
    get_aggfunc_by_name(name=name, func_params=params)


def test_get_aggfunc_by_name_errors() -> None:
    """Test aggregation function retrieval using wrong name."""
    with pytest.raises(ValueError, match="unknown. Please provide any of"):
        get_aggfunc_by_name(name="invalid", func_params=None)

    with pytest.raises(ValueError, match="list of limits"):
        get_aggfunc_by_name(name="winsorized_mean", func_params=None)

    with pytest.raises(ValueError, match="list of limits"):
        get_aggfunc_by_name(
            name="winsorized_mean", func_params={"limits": 0.1}
        )

    with pytest.raises(ValueError, match="list of two limits"):
        get_aggfunc_by_name(
            name="winsorized_mean", func_params={"limits": [0.2]}
        )

    with pytest.raises(ValueError, match="list of two"):
        get_aggfunc_by_name(
            name="winsorized_mean", func_params={"limits": [0.2, 0.7, 0.1]}
        )

    with pytest.raises(ValueError, match="must be between 0 and 1"):
        get_aggfunc_by_name(
            name="winsorized_mean", func_params={"limits": [-1, 0.7]}
        )

    with pytest.raises(ValueError, match="must be between 0 and 1"):
        get_aggfunc_by_name(
            name="winsorized_mean", func_params={"limits": [0.1, 2]}
        )


def test_winsorized_mean() -> None:
    """Test winsorized mean."""
    input = np.array([22, 4, 9, 8, 5, 3, 7, 2, 1, 6])
    output = winsorized_mean(input, limits=[0.1, 0.1])
    assert output == 5.5


@pytest.mark.parametrize(
    "data, axis, expected_value",
    [
        [np.array([[1, 1, 1, 2], [2, 2, 2, 3], [3, 3, 3, 1]]), -1, 0.4375],
        [np.array([[1, 2, 3], [1, 2, 3], [1, 2, 3], [2, 3, 1]]), 0, 0.4375],
        [np.array([[1, 1, 1, 2], [2, 2, 2, 3], [3, 3, 3, 1]]), 1, 0.4375],
    ],
)
def test_kendwall_w(
    data: np.ndarray, axis: int, expected_value: float
) -> None:
    """Test kendall_w function.

    Parameters
    ----------
    data : 2D np.ndarray
        The parametrized 2D data array.
    axis : int
        The parametrized axis.
    expected_value : float
        The parametrized expected value.

    """
    value = kendall_w(data, axis=axis)
    assert value == pytest.approx(expected_value)


def test_kendall_w_invalid_dimension() -> None:
    """Test kendall_w invalid dimension."""
    with pytest.raises(ValueError, match="no meaning"):
        kendall_w(np.array([1, 2]), axis=0)


def test_kendall_w_invalid_axis() -> None:
    """Test kendall_w invalid axis."""
    with pytest.raises(ValueError, match="Unknown axis"):
        kendall_w(np.array([[1, 2], [3, 4]]), axis=2)
