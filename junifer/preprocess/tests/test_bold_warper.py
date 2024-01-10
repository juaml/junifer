"""Provide tests for BOLDWarper."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import socket
from typing import TYPE_CHECKING, List, Tuple

import pytest

from junifer.datagrabber import DataladHCP1200, DMCC13Benchmark
from junifer.datareader import DefaultDataReader
from junifer.pipeline.utils import _check_ants, _check_fsl
from junifer.preprocess import BOLDWarper


if TYPE_CHECKING:
    from junifer.datagrabber import BaseDataGrabber


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


@pytest.mark.parametrize(
    "datagrabber, element",
    [
        [
            DMCC13Benchmark(
                types=["BOLD", "T1w", "Warp"],
                sessions=["wave1bas"],
                tasks=["Rest"],
                phase_encodings=["AP"],
                runs=["1"],
                native_t1w=True,
            ),
            ("f9057kp", "wave1bas", "Rest", "AP", "1"),
        ],
        [
            DataladHCP1200(
                tasks=["REST1"],
                phase_encodings=["LR"],
                ica_fix=True,
            ),
            ("100206", "REST1", "LR"),
        ],
    ],
)
@pytest.mark.skipif(_check_fsl() is False, reason="requires FSL to be in PATH")
@pytest.mark.skipif(
    _check_ants() is False, reason="requires ANTs to be in PATH"
)
@pytest.mark.skipif(
    socket.gethostname() != "juseless",
    reason="only for juseless",
)
def test_BOLDWarper_preprocess(
    datagrabber: "BaseDataGrabber", element: Tuple[str, ...]
) -> None:
    """Test BOLDWarper preprocess.

    Parameters
    ----------
    datagrabber : DataGrabber-like object
        The parametrized DataGrabber objects.
    element : tuple of str
        The parametrized elements.

    """
    with datagrabber as dg:
        # Read data
        element_data = DefaultDataReader().fit_transform(dg[element])
        # Preprocess data
        data_type, data = BOLDWarper(reference="T1w").preprocess(
            input=element_data["BOLD"],
            extra_input=element_data,
        )
        assert data_type == "BOLD"
        assert isinstance(data, dict)
