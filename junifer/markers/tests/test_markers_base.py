"""Provide tests for base marker."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import List, Optional

import pytest

from junifer.markers.base import BaseMarker


@pytest.mark.parametrize(
    "on, name, kind, expected_class, expected_name",
    [
        (["bold", "dwi"], None, "bold", "BaseMarker", "bold_BaseMarker"),
        (["bold", "dwi"], "mymarker", "dwi", "BaseMarker", "dwi_mymarker"),
    ],
)
def test_base_marker_meta(
    on: List[str],
    name: Optional[str],
    kind: str,
    expected_class: str,
    expected_name: str,
) -> None:
    """Test metadata for BaseMarker.

    Parameters
    ----------
    on : list of str
        The parametrized kind of data to work on.
    name : str or None
        The parametrized name of the marker.
    kind : str
        The parametrized kind of data to get metadata for.
    expected_class : str
        The paramtrized expected class of the marker.
    expected_name : str
        The parametrized expected name of the marker.

    """
    base = BaseMarker(on=on, name=name)
    t_meta = base.get_meta(kind=kind)
    assert t_meta["marker"]["class"] == expected_class
    assert t_meta["marker"]["name"] == expected_name


def test_BaseMarker() -> None:
    """Test base class."""
    base = BaseMarker(on=["bold", "dwi"], name="mymarker")
    input_ = {"bold": {"path": "test"}, "t2": {"path": "test"}}
    base.validate_input(input_)

    wrong_input = {"t2": {"path": "test"}}
    with pytest.raises(ValueError):
        base.validate_input(wrong_input)

    output = base.get_output_kind(input_)
    assert output is None

    with pytest.raises(NotImplementedError):
        base.fit_transform(input_)

    base.compute = lambda x: {"data": 1}

    out = base.fit_transform(input_)
    assert out["bold"]["data"] == 1
    assert out["bold"]["meta"]["marker"]["name"] == "bold_mymarker"
    assert out["bold"]["meta"]["marker"]["class"] == "BaseMarker"

    base2 = BaseMarker(on="bold", name="mymarker")
    base2.compute = lambda x: {"data": 1}
    out2 = base2.fit_transform(input_)
    assert out2["bold"]["data"] == 1
    assert out2["bold"]["meta"]["marker"]["name"] == "bold_mymarker"
    assert out2["bold"]["meta"]["marker"]["class"] == "BaseMarker"
