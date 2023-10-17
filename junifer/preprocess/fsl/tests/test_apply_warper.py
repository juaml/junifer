"""Provide tests for ApplyWarper."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import List

import pytest

# from junifer.datareader import DefaultDataReader
# from junifer.pipeline.utils import _check_fsl
from junifer.preprocess.fsl.apply_warper import _ApplyWarper


def test_ApplyWarper_init() -> None:
    """Test ApplyWarper init."""
    apply_warper = _ApplyWarper(reference="T1w", on="BOLD")
    assert apply_warper.ref == "T1w"
    assert apply_warper.on == "BOLD"
    assert apply_warper._on == ["BOLD"]


def test_ApplyWarper_get_valid_inputs() -> None:
    """Test ApplyWarper get_valid_inputs."""
    apply_warper = _ApplyWarper(reference="T1w", on="BOLD")
    assert apply_warper.get_valid_inputs() == ["BOLD"]


@pytest.mark.parametrize(
    "input_",
    [
        ["BOLD", "T1w", "Warp"],
        ["BOLD", "T1w"],
        ["BOLD"],
    ],
)
def test_ApplyWarper_get_output_type(input_: List[str]) -> None:
    """Test ApplyWarper get_output_type.

    Parameters
    ----------
    input_ : list of str
        The input data types.

    """
    apply_warper = _ApplyWarper(reference="T1w", on="BOLD")
    assert apply_warper.get_output_type(input_) == input_


@pytest.mark.skip(reason="requires testing dataset")
# @pytest.mark.skipif(
#     _check_fsl() is False, reason="requires fsl to be in PATH"
# )
def test_ApplyWarper__run_applywarp() -> None:
    """Test ApplyWarper _run_applywarp."""
    # Initialize datareader
    # reader = DefaultDataReader()
    # Initialize preprocessor
    # bold_warper = _ApplyWarper(reference="T1w", on="BOLD")
    # TODO(synchon): setup datagrabber and run pipeline


@pytest.mark.skip(reason="requires testing dataset")
# @pytest.mark.skipif(
#     _check_fsl() is False, reason="requires fsl to be in PATH"
# )
def test_ApplyWarper_preprocess() -> None:
    """Test ApplyWarper preprocess."""
    # Initialize datareader
    # reader = DefaultDataReader()
    # Initialize preprocessor
    # bold_warper = _ApplyWarper(reference="T1w", on="BOLD")
    # TODO(synchon): setup datagrabber and run pipeline
