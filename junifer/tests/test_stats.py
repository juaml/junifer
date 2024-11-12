"""Provide tests for stats."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Optional

import numpy as np
import pytest
from numpy.testing import assert_array_equal

from junifer.stats import count, get_aggfunc_by_name, select, winsorized_mean


@pytest.mark.parametrize(
    "name, params",
    [
        ("winsorized_mean", {"limits": [0.2, 0.7]}),
        ("mean", None),
        ("std", None),
        ("count", None),
        ("trim_mean", None),
        ("trim_mean", {"proportiontocut": 0.1}),
        ("mode", None),
        ("mode", {"keepdims": True}),
    ],
)
def test_get_aggfunc_by_name(name: str, params: Optional[dict]) -> None:
    """Test aggregation function retrieval by name.

    Parameters
    ----------
    name : str
        The parametrized name of the method name.
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

    with pytest.raises(ValueError, match="must be specified."):
        get_aggfunc_by_name(name="select", func_params=None)

    with pytest.raises(ValueError, match="must be specified, not both."):
        get_aggfunc_by_name(
            name="select", func_params={"pick": [0], "drop": [1]}
        )


def test_winsorized_mean() -> None:
    """Test winsorized mean."""
    input = np.array([22, 4, 9, 8, 5, 3, 7, 2, 1, 6])
    output = winsorized_mean(input, limits=[0.1, 0.1])
    assert output == 5.5


def test_count() -> None:
    """Test count."""
    input = np.zeros((10, 3))
    ax1 = np.ones(10) * 3
    ax2 = np.ones(3) * 10
    assert_array_equal(count(input, axis=-1), ax1)
    assert_array_equal(count(input, axis=1), ax1)
    assert_array_equal(count(input, axis=0), ax2)

    input = np.zeros((10, 0))
    ax1 = np.zeros(10)
    ax2 = np.zeros(0)

    assert_array_equal(count(input, axis=-1), ax1)
    assert_array_equal(count(input, axis=1), ax1)
    assert_array_equal(count(input, axis=0), ax2)


def test_select() -> None:
    """Test select."""
    input = np.arange(28).reshape(7, 4)

    with pytest.raises(ValueError, match="must be specified."):
        select(input, axis=2)

    with pytest.raises(ValueError, match="must be specified, not both."):
        select(input, pick=[1], drop=[2], axis=2)

    out1 = select(input, pick=[1], axis=0)
    assert_array_equal(out1, input[1:2, :])

    out2 = select(input, pick=[1, 4, 6], axis=0)
    assert_array_equal(out2, input[[1, 4, 6], :])

    out3 = select(input, drop=[0, 2, 3, 4, 5, 6], axis=0)
    assert_array_equal(out1, out3)

    out4 = select(input, drop=[0, 2, 3, 5], axis=0)
    assert_array_equal(out2, out4)

    out5 = select(input, drop=np.array([0, 2, 3, 5]), axis=0)  # type: ignore
    assert_array_equal(out2, out5)

    out6 = select(input, pick=np.array([1, 4, 6]), axis=0)  # type: ignore
    assert_array_equal(out2, out6)
