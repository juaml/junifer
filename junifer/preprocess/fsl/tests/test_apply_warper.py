"""Provide tests for ApplyWarper."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import socket
from pathlib import Path
from typing import List

import nibabel as nib
import pytest

from junifer.datagrabber import DataladHCP1200
from junifer.datareader import DefaultDataReader
from junifer.pipeline.utils import _check_fsl
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


@pytest.mark.skipif(_check_fsl() is False, reason="requires FSL to be in PATH")
@pytest.mark.skipif(
    socket.gethostname() != "juseless",
    reason="only for juseless",
)
def test_ApplyWarper__run_applywarp() -> None:
    """Test ApplyWarper _run_applywarp."""
    with DataladHCP1200(
        tasks=["REST1"],
        phase_encodings=["LR"],
        ica_fix=True,
    ) as dg:
        # Read data
        element_data = DefaultDataReader().fit_transform(
            dg[("100206", "REST1", "LR")]
        )
        # Preprocess data
        warped_data, resampled_ref_path = _ApplyWarper(
            reference="T1w", on="BOLD"
        )._run_applywarp(
            input_data=element_data["BOLD"],
            ref_path=element_data["T1w"]["path"],
            warp_path=element_data["Warp"]["path"],
        )
        assert isinstance(warped_data, nib.Nifti1Image)
        assert isinstance(resampled_ref_path, Path)


@pytest.mark.skipif(_check_fsl() is False, reason="requires FSL to be in PATH")
@pytest.mark.skipif(
    socket.gethostname() != "juseless",
    reason="only for juseless",
)
def test_ApplyWarper_preprocess() -> None:
    """Test ApplyWarper preprocess."""
    with DataladHCP1200(
        tasks=["REST1"],
        phase_encodings=["LR"],
        ica_fix=True,
    ) as dg:
        # Read data
        element_data = DefaultDataReader().fit_transform(
            dg[("100206", "REST1", "LR")]
        )
        # Preprocess data
        data_type, data = _ApplyWarper(reference="T1w", on="BOLD").preprocess(
            input=element_data["BOLD"],
            extra_input=element_data,
        )
        assert isinstance(data_type, str)
        assert isinstance(data, dict)
