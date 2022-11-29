"""Provide tests for data utils."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from typing import List

import numpy as np
import pytest

from junifer.data.utils import closest_resolution


@pytest.mark.parametrize(
    "resolution, valid_resolutions, expected",
    [
        (1.0, [1.0, 2.0, 3.0], 1.0),
        (1.1, [1.0, 2.0, 3.0], 1.0),
        (0.9, [1.0, 2.0, 3.0], 1.0),
        (2.1, [1.0, 2.0, 3.0], 2.0),
        (2.0, [1.0, 2.0, 3.0], 2.0),
        (4.0, [1.0, 2.0, 3.0], 3.0),
        (None, [1.0, 2.0, 3.0], 1.0),
    ],
)
def test_closest_resolution(
    resolution: float, valid_resolutions: List[float], expected: float
):
    """Test closest_resolution.

    Parameters
    ----------
    resolution: float
        The resolution to test.
    valid_resolutions: list of float
        The valid resolutions.
    expected: float
        The expected result.
    """
    assert closest_resolution(resolution, valid_resolutions) == expected
    assert (
        closest_resolution(resolution, np.array(valid_resolutions)) == expected
    )
