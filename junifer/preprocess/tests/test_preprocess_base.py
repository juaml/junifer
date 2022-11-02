"""Provide tests for BasePreprocessor."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import pytest

from junifer.preprocess.base import BasePreprocessor


def test_base_preprocessor_abstractness() -> None:
    """Test BasePreprocessor is abstract base class."""
    with pytest.raises(TypeError, match=r"abstract"):
        BasePreprocessor(on=["BOLD"])  # type: ignore


def test_base_preprocessor_subclassing() -> None:
    """Test proper subclassing of BasePreprocessor."""
    # Create concrete class
    class MyBasePreprocessor(BasePreprocessor):
        def get_valid_inputs(self):
            return ["BOLD", "T1w"]

        def get_output_kind(self, input):
            return ["timeseries"]

        def preprocess(self, input, extra_input):
            input["data"] = f"mofidied_{input['data']}"
            return "BOLD", input

    with pytest.raises(ValueError, match=r"cannot be computed on \['T2w'\]"):
        MyBasePreprocessor(on=["BOLD", "T2w"])

    with pytest.raises(ValueError, match=r"cannot be computed on \['T2w'\]"):
        MyBasePreprocessor(on="T2w")

    # Create input for marker
    input_ = {
        "meta": {"datagrabber": "dg", "element": "elem", "datareader": "dr"},
        "BOLD": {
            "path": ".",
            "data": "data",
        },
        "T1w": {
            "path": ".",
            "data": "data",
        },
    }
    prep = MyBasePreprocessor(on=["BOLD"])

    with pytest.raises(ValueError, match="not have the required data"):
        prep.validate_input(["T1w"])

    output = prep.fit_transform(input=input_)  # process
    # Check output
    assert "BOLD" in output
    assert "data" in output["BOLD"]
    assert output["BOLD"]["data"] == "mofidied_data"
    assert "path" in output["BOLD"]
    assert "meta" in output["BOLD"]

    assert "T1w" in output
    assert "data" in output["T1w"]
    assert output["T1w"]["data"] == "data"
