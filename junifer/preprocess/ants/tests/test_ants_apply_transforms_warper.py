"""Provide tests for AntsApplyTransformsWarper."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import socket
from pathlib import Path
from typing import List

import nibabel as nib
import pytest

from junifer.datagrabber import DMCC13Benchmark
from junifer.datareader import DefaultDataReader
from junifer.pipeline.utils import _check_ants
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


@pytest.mark.skipif(
    _check_ants() is False, reason="requires ANTs to be in PATH"
)
@pytest.mark.skipif(
    socket.gethostname() != "juseless",
    reason="only for juseless",
)
def test_AntsApplyTransformsWarper__run_apply_transform() -> None:
    """Test AntsApplyTransformsWarper _run_apply_transform."""
    with DMCC13Benchmark(
        types=["BOLD", "T1w", "Warp"],
        sessions=["wave1bas"],
        tasks=["Rest"],
        phase_encodings=["AP"],
        runs=["1"],
        native_t1w=True,
    ) as dg:
        # Read data
        element_data = DefaultDataReader().fit_transform(
            dg[("f9057kp", "wave1bas", "Rest", "AP", "1")]
        )
        # Preprocess data
        warped_data, resampled_ref_path = _AntsApplyTransformsWarper(
            reference="T1w", on="BOLD"
        )._run_apply_transforms(
            input_data=element_data["BOLD"],
            ref_path=element_data["T1w"]["path"],
            warp_path=element_data["Warp"]["path"],
        )
        assert isinstance(warped_data, nib.Nifti1Image)
        assert isinstance(resampled_ref_path, Path)


@pytest.mark.skipif(
    _check_ants() is False, reason="requires ANTs to be in PATH"
)
@pytest.mark.skipif(
    socket.gethostname() != "juseless",
    reason="only for juseless",
)
def test_AntsApplyTransformsWarper_preprocess() -> None:
    """Test AntsApplyTransformsWarper preprocess."""
    with DMCC13Benchmark(
        types=["BOLD", "T1w", "Warp"],
        sessions=["wave1bas"],
        tasks=["Rest"],
        phase_encodings=["AP"],
        runs=["1"],
        native_t1w=True,
    ) as dg:
        # Read data
        element_data = DefaultDataReader().fit_transform(
            dg[("f9057kp", "wave1bas", "Rest", "AP", "1")]
        )
        # Preprocess data
        data_type, data = _AntsApplyTransformsWarper(
            reference="T1w", on="BOLD"
        ).preprocess(
            input=element_data["BOLD"],
            extra_input=element_data,
        )
        assert isinstance(data_type, str)
        assert isinstance(data, dict)
