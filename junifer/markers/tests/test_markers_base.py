"""Provide tests for base marker."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import pytest

from junifer.markers.base import BaseMarker


def test_base_marker_abstractness() -> None:
    """Test BaseMarker is abstract base class."""
    with pytest.raises(TypeError, match=r"abstract"):
        BaseMarker(on=["BOLD"])  # type: ignore


def test_base_marker_subclassing() -> None:
    """Test proper subclassing of BaseMarker."""
    # Create concrete class
    class MyBaseMarker(BaseMarker):
        def get_valid_inputs(self):
            return ["BOLD", "T1w"]

        def get_output_kind(self, input):
            return ["timeseries"]

        def compute(self, input, extra_input):
            return {
                "data": "data",
                "columns": "columns",
                "row_names": "row_names",
            }

        def store(self, kind, out, storage):
            return super().store(kind=kind, out=out, storage=storage)

    with pytest.raises(ValueError, match=r"cannot be computed on \['T2w'\]"):
        MyBaseMarker(on=["BOLD", "T2w"])

    # Create input for marker
    input_ = {
        "meta": {"datagrabber": "dg", "element": "elem", "datareader": "dr"},
        "BOLD": {
            "path": ".",
            "data": "data",
        },
    }
    marker = MyBaseMarker(on=["BOLD"])

    with pytest.raises(ValueError, match="not have the required data"):
        marker.validate_input(["T1w"])

    output = marker.fit_transform(input=input_)  # process
    # Check output
    assert "BOLD" in output
    assert "data" in output["BOLD"]
    assert "columns" in output["BOLD"]
    assert "row_names" in output["BOLD"]
    assert "meta" in output["BOLD"]
    assert "datagrabber" in output["BOLD"]["meta"]
    assert "element" in output["BOLD"]["meta"]
    assert "datareader" in output["BOLD"]["meta"]

    # Check no implementation check
    with pytest.raises(NotImplementedError):
        marker.store(kind="kind", out="out", storage="storage")  # type: ignore

    # Check attributes
    assert marker.name == "MyBaseMarker"
