"""Provide tests for stats."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Dict, Optional

import pytest

from junifer.stats import get_aggfunc_by_name


@pytest.mark.parametrize(
    "name, params",
    [
        ("winsorized_mean", {"limits": [0.2, 0.7]}),
        ("mean", None),
        ("std", None),
        ("trim_mean", None),
    ],
)
def test_get_aggfunc_by_name(name: str, params: Optional[Dict]) -> None:
    """Test aggregation function retrieval by name."""
    get_aggfunc_by_name(name=name, func_params=params)


@pytest.mark.skip(reason="test not implemented")
def test_winsorized_mean() -> None:
    """Test winsorized mean computation."""
    ...
