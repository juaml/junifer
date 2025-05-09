"""Provide tests for TemporalSlicer."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from contextlib import AbstractContextManager, nullcontext
from typing import Optional

import pytest

from junifer.datareader import DefaultDataReader
from junifer.preprocess import TemporalSlicer
from junifer.testing.datagrabbers import PartlyCloudyTestingDataGrabber


@pytest.mark.parametrize(
    "start, stop, duration, t_r, expected_dim, expect",
    (
        [
            0.0,
            168.0,
            None,
            2.0,
            84,
            pytest.raises(RuntimeError, match="No temporal slicing"),
        ],  # t_r from doc is 2.0
        [0.0, 167.0, None, 2.0, 83, nullcontext()],  # t_r from doc is 2.0
        [
            0.0,
            None,
            None,
            2.0,
            84,
            pytest.raises(RuntimeError, match="No temporal slicing"),
        ],  # total with no end
        [2.0, None, None, 2.0, 83, nullcontext()],  # total with no end
        [0.0, 84.0, None, 2.0, 42, nullcontext()],  # first half
        [0.0, -85.0, None, 2.0, 42, nullcontext()],  # first half from end
        [84.0, -1.0, None, 2.0, 42, nullcontext()],  # second half
        [
            33.0,
            -33.0,
            33.0,
            2.0,
            42,
            pytest.raises(RuntimeError, match="`stop` should be None"),
        ],
        [10.0, None, 30.0, 2.0, 15, nullcontext()],
        [
            0.0,
            168.0,
            None,
            None,
            168,
            pytest.raises(RuntimeError, match="No temporal slicing"),
        ],  # t_r from image is 1.0
        [0.0, 167.0, None, None, 167, nullcontext()],  # t_r from image is 1.0
        [
            0.0,
            None,
            None,
            None,
            168,
            pytest.raises(RuntimeError, match="No temporal slicing"),
        ],  # total with no end
        [0.0, 84.0, None, None, 84, nullcontext()],  # first half
        [0.0, -85.0, None, None, 84, nullcontext()],  # first half from end
        [84.0, -1.0, None, None, 84, nullcontext()],  # second half
        [
            33.0,
            -33.0,
            33.0,
            None,
            84,
            pytest.raises(RuntimeError, match="`stop` should be None"),
        ],
        [10.0, None, 30.0, None, 30, nullcontext()],
        [
            -1.0,
            None,
            None,
            None,
            84,
            pytest.raises(ValueError, match="`start` cannot be negative"),
        ],
        [
            0.0,
            500.0,
            None,
            2.0,
            42,
            pytest.raises(IndexError, match="Calculated stop index:"),
        ],
    ),
)
def test_TemporalSlicer(
    start: float,
    stop: Optional[float],
    duration: Optional[float],
    t_r: Optional[float],
    expected_dim: int,
    expect: AbstractContextManager,
) -> None:
    """Test TemporalSlicer.

    Parameters
    ----------
    start : float
        The parametrized start.
    stop : float or None
        The parametrized stop.
    duration : float or None
        The parametrized duration.
    t_r : float or None
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
                start=start,  # in seconds
                stop=stop,  # in seconds
                duration=duration,  # in seconds
                t_r=t_r,  # in seconds
            ).fit_transform(element_data)

            # Check image data dim
            assert output["BOLD"]["data"].shape[3] == expected_dim
            # Check confounds dim
            assert output["BOLD"]["confounds"]["data"].shape[0] == expected_dim
