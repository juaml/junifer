"""Provide tests for TemporalFilter."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Optional

import pytest

from junifer.datareader import DefaultDataReader
from junifer.preprocess import TemporalFilter
from junifer.testing.datagrabbers import PartlyCloudyTestingDataGrabber


@pytest.mark.parametrize(
    "detrend, standardize, low_pass, high_pass, t_r",
    (
        [
            True,
            True,
            None,
            None,
            None,
        ],
        [
            False,
            True,
            0.1,
            None,
            None,
        ],
        [
            True,
            False,
            None,
            0.08,
            None,
        ],
        [
            False,
            False,
            None,
            None,
            2,
        ],
        [
            True,
            True,
            0.1,
            0.08,
            2,
        ],
    ),
)
def test_TemporalFilter(
    detrend: bool,
    standardize: bool,
    low_pass: Optional[float],
    high_pass: Optional[float],
    t_r: Optional[float],
) -> None:
    """Test TemporalFilter.

    Parameters
    ----------
    detrend : bool
        The parametrized detrending flag.
    standardize : bool
        The parametrized standardization flag.
    low_pass : float or None
        The parametrized low pass value.
    high_pass : float or None
        The parametrized high pass value.
    t_r : float or None
        The parametrized repetition time.
    expect : typing.ContextManager
        The parametrized ContextManager object.

    """
    with PartlyCloudyTestingDataGrabber() as dg:
        # Read data
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        # Preprocess data
        output = TemporalFilter(
            detrend=detrend,
            standardize=standardize,
            low_pass=low_pass,
            high_pass=high_pass,
            t_r=t_r,
        ).fit_transform(element_data)

        assert isinstance(output, dict)
