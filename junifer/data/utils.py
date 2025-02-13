"""Provide utilities for data module."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from collections.abc import MutableMapping
from pathlib import Path
from typing import Optional, Union

import datalad.api as dl
import numpy as np
from datalad.support.exceptions import IncompleteResultsError

from ..utils import config, logger, raise_error


__all__ = [
    "check_dataset",
    "closest_resolution",
    "fetch_file_via_datalad",
    "get_native_warper",
]


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


def check_dataset() -> dl.Dataset:
    """Get or install junifer-data dataset.

    Returns
    -------
    datalad.api.Dataset
        The junifer-data dataset.

    Raises
    ------
    RuntimeError
        If there is a problem cloning the dataset.

    """
    # Check config and set default if not passed
    data_dir = config.get("data.location")
    if data_dir is not None:
        data_dir = Path(data_dir)
    else:
        data_dir = Path().home() / "junifer_data"

    # Check if the dataset is installed at storage path;
    # else clone a fresh copy
    if dl.Dataset(data_dir).is_installed():
        logger.debug(f"Found existing junifer-data at: {data_dir.resolve()}")
        return dl.Dataset(data_dir)
    else:
        logger.debug(f"Cloning junifer-data to: {data_dir.resolve()}")
        # Clone dataset
        try:
            dataset = dl.clone(
                "https://github.com/juaml/junifer-data.git",
                path=data_dir,
                result_renderer="disabled",
            )
        except IncompleteResultsError as e:
            raise_error(
                msg=f"Failed to clone junifer-data: {e.failed}",
                klass=RuntimeError,
            )
        else:
            logger.debug(
                f"Successfully cloned junifer-data to: "
                f"{data_dir.resolve()}"
            )
            return dataset


def fetch_file_via_datalad(dataset: dl.Dataset, file_path: Path) -> Path:
    """Fetch `file_path` from `dataset` via datalad.

    Parameters
    ----------
    dataset : datalad.api.Dataset
        The datalad dataset to fetch files from.
    file_path : pathlib.Path
        The file path to fetch.

    Returns
    -------
    pathlib.Path
        Resolved fetched file path.

    Raises
    ------
    RuntimeError
        If there is a problem fetching the file.

    """
    try:
        got = dataset.get(file_path, result_renderer="disabled")
    except IncompleteResultsError as e:
        raise_error(
            msg=f"Failed to get file from dataset: {e.failed}",
            klass=RuntimeError,
        )
    else:
        got_path = Path(got[0]["path"])
        # Conditional logging based on file fetch
        status = got[0]["status"]
        if status == "ok":
            logger.info(f"Successfully fetched file: {got_path.resolve()}")
            return got_path
        elif status == "notneeded":
            logger.debug(f"Found existing file: {got_path.resolve()}")
            return got_path
        else:
            raise_error(
                msg=f"Failed to fetch file: {got_path.resolve()}",
                klass=RuntimeError,
            )
