"""Provide utilities for data module."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from collections.abc import MutableMapping
from pathlib import Path
from typing import Optional, Union

import numpy as np

from ..utils import config, logger, raise_error


__all__ = [
    "JUNIFER_DATA_HEXSHA",
    "JUNIFER_DATA_PARAMS",
    "JUNIFER_DATA_VERSION",
    "closest_resolution",
    "get_dataset_path",
    "get_native_warper",
]


# junifer-data version constant
JUNIFER_DATA_VERSION = "2"

# junifer-data hexsha constant
JUNIFER_DATA_HEXSHA = "015712689254c052fa64bca19f0f2da342e664ac"

JUNIFER_DATA_PARAMS = {
    "tag": JUNIFER_DATA_VERSION,
    "hexsha": JUNIFER_DATA_HEXSHA,
}


def closest_resolution(
    resolution: Optional[Union[float, int]],
    valid_resolution: Union[list[float], list[int], np.ndarray],
) -> Union[float, int]:
    """Find the closest resolution.

    Parameters
    ----------
    resolution : float or int, optional
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


def get_native_warper(
    target_data: MutableMapping,
    other_data: MutableMapping,
    inverse: bool = False,
) -> dict:
    """Get correct warping specification for native space.

    Parameters
    ----------
    target_data : dict
        The target data from the pipeline data object.
    other_data : dict
        The other data in the pipeline data object.
    inverse : bool, optional
        Whether to get the inverse warping specification (default False).

    Returns
    -------
    dict
        The correct warping specification.

    Raises
    ------
    RuntimeError
        If no warper or multiple possible warpers are found.

    """
    # Get possible warpers
    possible_warpers = []
    for entry in other_data["Warp"]:
        if not inverse:
            if (
                entry["src"] == target_data["prewarp_space"]
                and entry["dst"] == "native"
            ):
                possible_warpers.append(entry)
        else:
            if (
                entry["dst"] == target_data["prewarp_space"]
                and entry["src"] == "native"
            ):
                possible_warpers.append(entry)

    # Check for no warper
    if not possible_warpers:
        raise_error(
            klass=RuntimeError,
            msg="Could not find correct warping specification",
        )

    # Check for multiple possible warpers
    if len(possible_warpers) > 1:
        raise_error(
            klass=RuntimeError,
            msg=(
                "Cannot proceed as multiple warping specification found, "
                "adjust either the DataGrabber or the working space: "
                f"{possible_warpers}"
            ),
        )

    return possible_warpers[0]


def get_dataset_path() -> Optional[Path]:
    """Get junifer-data dataset path.

    Returns
    -------
    pathlib.Path or None
        Path to the dataset or None.

    """
    return (
        Path(config.get("data.location"))
        if config.get("data.location") is not None
        else None
    )
