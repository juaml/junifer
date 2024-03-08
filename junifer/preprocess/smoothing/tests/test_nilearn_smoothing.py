"""Provide tests for NilearnSmoothing."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL


import pytest

from junifer.datareader import DefaultDataReader
from junifer.preprocess import NilearnSmoothing
from junifer.testing.datagrabbers import SPMAuditoryTestingDataGrabber


def test_NilearnSmoothing_init() -> None:
    """Test NilearnSmoothing init."""
    smoothing = NilearnSmoothing(fwhm=None)
    assert smoothing._on == ["T1w", "T2w", "BOLD"]


def test_NilearnSmoothing_get_valid_input() -> None:
    """Test NilearnSmoothing get_valid_inputs."""
    smoothing = NilearnSmoothing(fwhm=None)
    assert smoothing.get_valid_inputs() == ["T1w", "T2w", "BOLD"]


def test_NilearnSmoothing_get_output_type() -> None:
    """Test NilearnSmoothing get_output_type."""
    smoothing = NilearnSmoothing(fwhm=None)
    assert smoothing.get_output_type("BOLD") == "BOLD"


@pytest.mark.parametrize(
    "data_type",
    [
        "T1w",
        "BOLD",
    ],
)
def test_NilearnSmoothing_preprocess(data_type: str) -> None:
    """Test NilearnSmoothing preprocess.

    Parameters
    ----------
    data_type : str
        The parametrized data type.

    """
    with SPMAuditoryTestingDataGrabber() as dg:
        # Read data
        element_data = DefaultDataReader().fit_transform(dg["sub001"])
        # Preprocess data
        data, _ = NilearnSmoothing(fwhm="fast").preprocess(
            input=element_data[data_type]
        )
        assert isinstance(data, dict)
