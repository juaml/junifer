"""Provide tests for ApplyWarper."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import socket

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
