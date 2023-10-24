"""Provide tests for BOLDWarper."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import List

import pytest

# from junifer.datareader import DefaultDataReader
# from junifer.pipeline.utils import _check_fsl
from junifer.preprocess.fsl import BOLDWarper


def test_BOLDWarper_init() -> None:
    """Test BOLDWarper init."""
    bold_warper = BOLDWarper(reference="T1w")
    assert bold_warper._on == ["BOLD"]


def test_BOLDWarper_get_valid_inputs() -> None:
    """Test BOLDWarper get_valid_inputs."""
    bold_warper = BOLDWarper(reference="T1w")
    assert bold_warper.get_valid_inputs() == ["BOLD"]


@pytest.mark.parametrize(
    "input_",
    [
        ["BOLD", "T1w", "Warp"],
        ["BOLD", "T1w"],
        ["BOLD"],
    ],
)
def test_BOLDWarper_get_output_type(input_: List[str]) -> None:
    """Test BOLDWarper get_output_type.

    Parameters
    ----------
    input_ : list of str
        The input data types.

    """
    bold_warper = BOLDWarper(reference="T1w")
    assert bold_warper.get_output_type(input_) == input_


@pytest.mark.skip(reason="requires testing dataset")
# @pytest.mark.skipif(
#     _check_fsl() is False, reason="requires fsl to be in PATH"
# )
def test_BOLDWarper_preprocess() -> None:
    """Test BOLDWarper preprocess."""
    # Initialize datareader
    # reader = DefaultDataReader()
    # Initialize preprocessor
    # bold_warper = BOLDWarper(reference="T1w")
    # TODO(synchon): setup datagrabber and run pipeline
