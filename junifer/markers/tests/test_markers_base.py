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


def test_compute_parameters() -> None:
    """Test compute parameters."""
    base = BaseMarker(on=["bold", "dwi"], name="mymarker")
    base.compute = lambda x, y: {  # type: ignore
        "data": x.keys(), "extra": y.keys()}
    input_ = {"bold": {"path": "test"}, "t2": {"path": "test"}}
    out = base.fit_transform(
        input_,
    )
    assert list(out["bold"]["data"]) == ["path"]
    assert list(out["bold"]["extra"]) == ["t2"]


def test_BaseMarker() -> None:
    """Test base class."""
    base = BaseMarker(on=["bold", "dwi"], name="mymarker")
    input_ = {"bold": {"path": "test"}, "t2": {"path": "test"}}
    base.validate_input(list(input_.keys()))

    wrong_input = {"t2": {"path": "test"}}
    with pytest.raises(ValueError):
        base.validate_input(list(wrong_input.keys()))

    with pytest.raises(NotImplementedError):
        base.get_output_kind(list(wrong_input.keys()))

    with pytest.raises(NotImplementedError):
        base.fit_transform(input_)

    with pytest.raises(NotImplementedError):
        base.store("bold", {}, None)

    base.compute = lambda x, y: {"data": 1}  # type: ignore

    out = base.fit_transform(input_)
    assert out["bold"]["data"] == 1
    assert out["bold"]["meta"]["marker"]["name"] == "bold_mymarker"
    assert out["bold"]["meta"]["marker"]["class"] == "BaseMarker"
    assert "dwi" not in out

    base2 = BaseMarker(on="bold", name="mymarker")
    base2.compute = lambda x, y: {"data": 1}  # type: ignore
    out2 = base2.fit_transform(input_)
    assert out2["bold"]["data"] == 1
    assert out2["bold"]["meta"]["marker"]["name"] == "bold_mymarker"
    assert out2["bold"]["meta"]["marker"]["class"] == "BaseMarker"
