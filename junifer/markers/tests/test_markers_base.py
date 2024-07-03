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

        _MARKER_INOUT_MAPPINGS = {  # noqa: RUF012
            "BOLD": {
                "feat_1": "timeseries",
            },
        }

        def __init__(self, on, name=None) -> None:
            self.parameter = 1
            super().__init__(on, name)

        def compute(self, input, extra_input):
            return {
                "feat_1": {
                    "data": "data",
                    "col_names": ["columns"],
                },
            }

    with pytest.raises(ValueError, match=r"cannot be computed on \['T1w'\]"):
        MyBaseMarker(on=["BOLD", "T1w"])

    # Create input for marker
    input_ = {
        "BOLD": {
            "path": ".",
            "data": "data",
            "meta": {
                "datagrabber": "dg",
                "element": "elem",
                "datareader": "dr",
            },
        },
    }
    marker = MyBaseMarker(on=["BOLD"])

    with pytest.raises(ValueError, match="not have the required data"):
        marker.validate_input(["T1w"])

    assert marker.validate_input(["BOLD", "Other"]) == ["BOLD"]

    output = marker.fit_transform(input=input_)  # process
    # Check output
    assert "BOLD" in output
    assert "data" in output["BOLD"]["feat_1"]
    assert "col_names" in output["BOLD"]["feat_1"]

    assert "meta" in output["BOLD"]["feat_1"]
    meta = output["BOLD"]["feat_1"]["meta"]
    assert "datagrabber" in meta
    assert "element" in meta
    assert "datareader" in meta
    assert "marker" in meta
    assert "name" in meta["marker"]
    assert "parameter" in meta["marker"]
    assert meta["marker"]["parameter"] == 1

    # Check attributes
    assert marker.name == "MyBaseMarker"

    # Add one extra input that will not be used to compute
    input_ = {
        "BOLD": {
            "path": ".",
            "data": "data",
            "meta": {
                "datagrabber": "dg",
                "element": "elem",
                "datareader": "dr",
            },
        },
        "T2": {
            "path": ".",
            "data": "data",
            "meta": {
                "datagrabber": "dg",
                "element": "elem",
                "datareader": "dr",
            },
        },
    }
    marker = MyBaseMarker(on=["BOLD"])
    output = marker.fit_transform(input=input_)  # process
    # Check output
    assert "BOLD" in output
    assert "T2" not in output
