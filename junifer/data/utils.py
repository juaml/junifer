"""Provide utilities for data module."""
from typing import List, Optional, Union

import numpy as np

from ..utils.logging import logger


def closest_resolution(
    resolution: Optional[float],
    valid_resolution: Union[List[float], List[int], np.ndarray],
) -> Union[float, int]:
    """Find the closest resolution.

    Parameters
    ----------
    resolution : float, optional
        The given resolution. If None, will return the highest resolution
        (default None).
    valid_resolution : list of float or int, or np.ndarray
        The array of valid resolutions.

    Returns
    -------
    float or int
        The closest valid resolution.
    """
    # Convert list of int to numpy.ndarray
    if not isinstance(valid_resolution, np.ndarray):
        valid_resolution = np.array(valid_resolution)

    if resolution is None:
        logger.info("Resolution set to None, using highest resolution.")
        closest = np.min(valid_resolution)
    elif any(x <= resolution for x in valid_resolution):
        # Case 1: get the highest closest resolution
        closest = np.max(valid_resolution[valid_resolution <= resolution])
    else:
        # Case 2: get the lower closest resolution
        closest = np.min(valid_resolution)

    return closest
