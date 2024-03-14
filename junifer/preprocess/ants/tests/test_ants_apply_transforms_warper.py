"""Provide tests for AntsApplyTransformsWarper."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import socket

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
