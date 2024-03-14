"""Provide tests for Smoothing."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL


import pytest

from junifer.datareader import DefaultDataReader
from junifer.preprocess import Smoothing
from junifer.testing.datagrabbers import SPMAuditoryTestingDataGrabber


@pytest.mark.parametrize(
    "data_type",
    ["T1w", "BOLD", None],
)
def test_Smoothing(data_type: str) -> None:
    """Test Smoothing.

    Parameters
    ----------
    data_type : str
        The parametrized data type.

    """
    with SPMAuditoryTestingDataGrabber() as dg:
        # Read data
        element_data = DefaultDataReader().fit_transform(dg["sub001"])
        # Preprocess data
        data, _ = Smoothing(
            using="nilearn",
            smoothing_params={"fwhm": "fast"},
            on=data_type,
        ).fit_transform(element_data)

        assert isinstance(data, dict)
