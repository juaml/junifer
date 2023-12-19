"""Provide tests for AntsApplyTransformsWarper."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import List

import pytest

# from junifer.datareader import DefaultDataReader
# from junifer.pipeline.utils import _check_ants
from junifer.preprocess.ants.ants_apply_transforms_warper import (
    _AntsApplyTransformsWarper,
)


def test_AntsApplyTransformsWarper_init() -> None:
    """Test AntsApplyTransformsWarper init."""
    ants_apply_transforms_warper = _AntsApplyTransformsWarper(
        reference="T1w", on="BOLD"
    )
    assert ants_apply_transforms_warper.ref == "T1w"
    assert ants_apply_transforms_warper.on == "BOLD"
    assert ants_apply_transforms_warper._on == ["BOLD"]


def test_AntsApplyTransformsWarper_get_valid_inputs() -> None:
    """Test AntsApplyTransformsWarper get_valid_inputs."""
    ants_apply_transforms_warper = _AntsApplyTransformsWarper(
        reference="T1w", on="BOLD"
    )
    assert ants_apply_transforms_warper.get_valid_inputs() == ["BOLD"]


@pytest.mark.parametrize(
    "input_",
    [
        ["BOLD", "T1w", "Warp"],
        ["BOLD", "T1w"],
        ["BOLD"],
    ],
)
def test_AntsApplyTransformsWarper_get_output_type(input_: List[str]) -> None:
    """Test AntsApplyTransformsWarper get_output_type.

    Parameters
    ----------
    input_ : list of str
        The input data types.

    """
    ants_apply_transforms_warper = _AntsApplyTransformsWarper(
        reference="T1w", on="BOLD"
    )
    assert ants_apply_transforms_warper.get_output_type(input_) == input_


@pytest.mark.skip(reason="requires testing dataset")
# @pytest.mark.skipif(
#     _check_ants() is False, reason="requires ANTs to be in PATH"
# )
def test_AntsApplyTransformsWarper__run_apply_transform() -> None:
    """Test AntsApplyTransformsWarper _run_apply_transform."""
    # Initialize datareader
    # reader = DefaultDataReader()
    # Initialize preprocessor
    # bold_warper = _AntsApplyTransformsWarper(reference="T1w", on="BOLD")
    # TODO(synchon): setup datagrabber and run pipeline


@pytest.mark.skip(reason="requires testing dataset")
# @pytest.mark.skipif(
#     _check_ants() is False, reason="requires ANTs to be in PATH"
# )
def test_AntsApplyTransformsWarper_preprocess() -> None:
    """Test AntsApplyTransformsWarper preprocess."""
    # Initialize datareader
    # reader = DefaultDataReader()
    # Initialize preprocessor
    # bold_warper = _AntsApplyTransformsWarper(reference="T1w", on="BOLD")
    # TODO(synchon): setup datagrabber and run pipeline
