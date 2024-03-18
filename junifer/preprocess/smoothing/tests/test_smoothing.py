"""Provide tests for Smoothing."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL


import pytest

from junifer.datareader import DefaultDataReader
from junifer.pipeline.utils import _check_afni, _check_fsl
from junifer.preprocess import Smoothing
from junifer.testing.datagrabbers import SPMAuditoryTestingDataGrabber


@pytest.mark.parametrize(
    "data_type",
    ["T1w", "BOLD"],
)
def test_Smoothing_nilearn(data_type: str) -> None:
    """Test Smoothing using nilearn.

    Parameters
    ----------
    data_type : str
        The parametrized data type.

    """
    with SPMAuditoryTestingDataGrabber() as dg:
        # Read data
        element_data = DefaultDataReader().fit_transform(dg["sub001"])
        # Preprocess data
        output = Smoothing(
            using="nilearn",
            on=data_type,
            smoothing_params={"fwhm": "fast"},
        ).fit_transform(element_data)

        assert isinstance(output, dict)


@pytest.mark.parametrize(
    "data_type",
    ["T1w", "BOLD"],
)
@pytest.mark.skipif(
    _check_afni() is False, reason="requires AFNI to be in PATH"
)
def test_Smoothing_afni(data_type: str) -> None:
    """Test Smoothing using AFNI.

    Parameters
    ----------
    data_type : str
        The parametrized data type.

    """
    with SPMAuditoryTestingDataGrabber() as dg:
        # Read data
        element_data = DefaultDataReader().fit_transform(dg["sub001"])
        # Preprocess data
        output = Smoothing(
            using="afni",
            on=data_type,
            smoothing_params={"fwhm": 3},
        ).fit_transform(element_data)

        assert isinstance(output, dict)


@pytest.mark.parametrize(
    "data_type",
    ["T1w", "BOLD"],
)
@pytest.mark.skipif(_check_fsl() is False, reason="requires FSL to be in PATH")
def test_Smoothing_fsl(data_type: str) -> None:
    """Test Smoothing using FSL.

    Parameters
    ----------
    data_type : str
        The parametrized data type.

    """
    with SPMAuditoryTestingDataGrabber() as dg:
        # Read data
        element_data = DefaultDataReader().fit_transform(dg["sub001"])
        # Preprocess data
        output = Smoothing(
            using="fsl",
            on=data_type,
            smoothing_params={"brightness_threshold": 10.0, "fwhm": 3.0},
        ).fit_transform(element_data)

        assert isinstance(output, dict)
