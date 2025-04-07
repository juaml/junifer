"""Provide tests for TemporalSlicer."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import pytest

from junifer.datareader import DefaultDataReader
from junifer.preprocess import TemporalSlicer
from junifer.testing.datagrabbers import PartlyCloudyTestingDataGrabber


@pytest.mark.parametrize(
    "start, stop, t_r, expected_dim",
    (
        [0, 168, 2.0, 84],  # t_r from doc is 2.0
        [0, 168, None, 168],  # t_r from image is 1.0
    ),
)
def test_TemporalSlicer(
    start: int,
    stop: int,
    t_r: float,
    expected_dim: int,
) -> None:
    """Test TemporalSlicer.

    Parameters
    ----------
    start : int
        The parametrized start.
    stop : int
        The parametrized stop.
    t_r : float
        The parametrized TR.
    expected_dim : int
        The parametrized expected time dimension size.

    """

    with PartlyCloudyTestingDataGrabber() as dg:
        # Read data
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        # Preprocess data
        output = TemporalSlicer(
            start=start,
            stop=stop,  # in seconds
            t_r=t_r,  # in seconds
        ).fit_transform(element_data)

        assert output["BOLD"]["data"].shape[3] == expected_dim
