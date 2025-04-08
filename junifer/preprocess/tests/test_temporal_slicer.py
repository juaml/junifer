"""Provide tests for TemporalSlicer."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from contextlib import AbstractContextManager, nullcontext

import pytest

from junifer.datareader import DefaultDataReader
from junifer.preprocess import TemporalSlicer
from junifer.testing.datagrabbers import PartlyCloudyTestingDataGrabber


@pytest.mark.parametrize(
    "start, stop, t_r, expected_dim, expect",
    (
        [
            0,
            168,
            2.0,
            84,
            pytest.raises(RuntimeError, match="No temporal slicing"),
        ],  # t_r from doc is 2.0
        [0, 167, 2.0, 83, nullcontext()],  # t_r from doc is 2.0
        [
            0,
            None,
            2.0,
            84,
            pytest.raises(RuntimeError, match="No temporal slicing"),
        ],  # total with no end
        [2, None, 2.0, 83, nullcontext()],  # total with no end
        [0, 84, 2.0, 42, nullcontext()],  # first half
        [0, -85, 2.0, 42, nullcontext()],  # first half from end
        [84, -1, 2.0, 42, nullcontext()],  # second half
        [
            0,
            168,
            None,
            168,
            pytest.raises(RuntimeError, match="No temporal slicing"),
        ],  # t_r from image is 1.0
        [0, 167, None, 167, nullcontext()],  # t_r from image is 1.0
        [
            0,
            None,
            None,
            168,
            pytest.raises(RuntimeError, match="No temporal slicing"),
        ],  # total with no end
        [0, 84, None, 84, nullcontext()],  # first half
        [0, -85, None, 84, nullcontext()],  # first half from end
        [84, -1, None, 84, nullcontext()],  # second half
    ),
)
def test_TemporalSlicer(
    start: int,
    stop: int,
    t_r: float,
    expected_dim: int,
    expect: AbstractContextManager,
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
    expect : typing.ContextManager
        The parametrized ContextManager object.

    """

    with PartlyCloudyTestingDataGrabber() as dg:
        # Read data
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        # Preprocess data
        with expect:
            output = TemporalSlicer(
                start=start,
                stop=stop,  # in seconds
                t_r=t_r,  # in seconds
            ).fit_transform(element_data)

            assert output["BOLD"]["data"].shape[3] == expected_dim
