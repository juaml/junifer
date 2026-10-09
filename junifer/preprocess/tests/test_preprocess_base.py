"""Provide tests for BasePreprocessor."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from collections.abc import Sequence
from typing import ClassVar

import pytest

from junifer.preprocess.base import BasePreprocessor


def test_base_preprocessor_abstractness() -> None:
    """Test BasePreprocessor is abstract base class."""
    with pytest.raises(TypeError, match=r"abstract"):
        BasePreprocessor(on="BOLD")


def test_base_preprocessor_subclassing() -> None:
    """Test proper subclassing of BasePreprocessor."""

    # Create concrete class
    class MyBasePreprocessor(BasePreprocessor):
        _VALID_DATA_TYPES: ClassVar[Sequence[str]] = ["BOLD", "T1w"]

        parameter: int = 1

        def preprocess(self, input, extra_input=None):
            input["data"] = f"modified_{input['data']}"
            return input

    with pytest.raises(ValueError, match=r"cannot be computed on \['T2w'\]"):
        MyBasePreprocessor(on=["BOLD", "T2w"])

    with pytest.raises(ValueError, match=r"cannot be computed on \['T2w'\]"):
        MyBasePreprocessor(on="T2w")

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
        "T1w": {
            "path": ".",
            "data": "data",
            "meta": {
                "datagrabber": "dg",
                "element": "elem",
                "datareader": "dr",
            },
        },
    }
    prep = MyBasePreprocessor(on="BOLD")

    with pytest.raises(ValueError, match="not have the required data"):
        prep.validate_input(["T1w"])

    output = prep.fit_transform(input=input_)  # process
    # Check output
    assert "BOLD" in output
    assert "data" in output["BOLD"]
    assert output["BOLD"]["data"] == "modified_data"
    assert "path" in output["BOLD"]
    assert "meta" in output["BOLD"]

    meta = output["BOLD"]["meta"]
    assert "preprocess" in meta
    assert len(meta["preprocess"]) == 1
    assert "class" in meta["preprocess"][0]
    assert "MyBasePreprocessor" == meta["preprocess"][0]["class"]
    assert "parameter" in meta["preprocess"][0]
    assert 1 == meta["preprocess"][0]["parameter"]

    # A second preprocessor is recorded after the first one
    output = MyBasePreprocessor(on="BOLD", parameter=2).fit_transform(
        input=output
    )
    assert [x["parameter"] for x in output["BOLD"]["meta"]["preprocess"]] == [
        1,
        2,
    ]

    assert "T1w" in output
    assert "data" in output["T1w"]
    assert output["T1w"]["data"] == "data"
