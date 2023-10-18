"""Provide functions for list of coordinates."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import typing
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike

from ..utils.logging import logger, raise_error, warn_with_log


# Path to the VOIs
_vois_path = Path(__file__).parent / "VOIs"

# Path to the metadata of the VOIs
_vois_meta_path = _vois_path / "meta"

# A dictionary containing all supported coordinates and their respective file
# or data.

# The built-in coordinates are files that are shipped with the package in the
# data/VOIs directory. The user can also register their own coordinates, which
# will be stored as numpy arrays in the dictionary.
_available_coordinates: Dict[
    str, Union[Path, Dict[str, Union[ArrayLike, List[str]]]]
] = {
    "CogAC": _vois_meta_path / "CogAC_VOIs.txt",
    "CogAR": _vois_meta_path / "CogAR_VOIs.txt",
    "DMNBuckner": _vois_meta_path / "DMNBuckner_VOIs.txt",
    "eMDN": _vois_meta_path / "eMDN_VOIs.txt",
    "Empathy": _vois_meta_path / "Empathy_VOIs.txt",
    "eSAD": _vois_meta_path / "eSAD_VOIs.txt",
    "extDMN": _vois_meta_path / "extDMN_VOIs.txt",
    "Motor": _vois_meta_path / "Motor_VOIs.txt",
    "MultiTask": _vois_meta_path / "MultiTask_VOIs.txt",
    "PhysioStress": _vois_meta_path / "PhysioStress_VOIs.txt",
    "Rew": _vois_meta_path / "Rew_VOIs.txt",
    "Somatosensory": _vois_meta_path / "Somatosensory_VOIs.txt",
    "ToM": _vois_meta_path / "ToM_VOIs.txt",
    "VigAtt": _vois_meta_path / "VigAtt_VOIs.txt",
    "WM": _vois_meta_path / "WM_VOIs.txt",
    "Power": _vois_meta_path / "Power2011_MNI_VOIs.txt",
    "Power2011": _vois_meta_path / "Power2011_MNI_VOIs.txt",
    "Dosenbach": _vois_meta_path / "Dosenbach2010_MNI_VOIs.txt",
    "Power2013": _vois_meta_path / "Power2013_MNI_VOIs.tsv",
}


def register_coordinates(
    name: str,
    coordinates: ArrayLike,
    voi_names: List[str],
    overwrite: Optional[bool] = False,
) -> None:
    """Register a custom user coordinates.

    Parameters
    ----------
    name : str
        The name of the coordinates.
    coordinates : numpy.ndarray
        The coordinates. This should be a 2-dimensional array with three
        columns. Each row corresponds to a volume-of-interest (VOI) and each
        column corresponds to a spatial dimension (i.e. x, y, and
        z-coordinates).
    voi_names : list of str
        The names of the VOIs.
    overwrite : bool, optional
        If True, overwrite an existing list of coordinates with the same name.
        Does not apply to built-in coordinates (default False).

    Raises
    ------
    ValueError
        If the coordinates name is already registered and overwrite is set to
        False or if the coordinates name is a built-in coordinates or if the
        ``coordinates`` is not a 2D array or if coordinate value does not have
        3 components or if the ``voi_names`` shape does not match the
        ``coordinates`` shape.
    TypeError
        If ``coordinates`` is not a ``numpy.ndarray``.

    """
    if name in _available_coordinates:
        if isinstance(_available_coordinates[name], Path):
            raise_error(
                f"Coordinates {name} already registered as built-in "
                "coordinates."
            )
        if overwrite is True:
            logger.info(f"Overwriting coordinates {name}")
        else:
            raise_error(
                f"Coordinates {name} already registered. "
                "Set `overwrite=True` to update its value."
            )

    if not isinstance(coordinates, np.ndarray):
        raise_error(
            f"Coordinates must be a `numpy.ndarray`, not {type(coordinates)}.",
            klass=TypeError,
        )
    if coordinates.ndim != 2:
        raise_error(
            f"Coordinates must be a 2D array, not {coordinates.ndim}D."
        )
    if coordinates.shape[1] != 3:
        raise_error(
            f"Each coordinate must have 3 values, not {coordinates.shape[1]} "
        )
    if len(voi_names) != coordinates.shape[0]:
        raise_error(
            f"Length of `voi_names` ({len(voi_names)}) does not match the "
            f"number of `coordinates` ({coordinates.shape[0]})."
        )
    _available_coordinates[name] = {
        "coords": coordinates,
        "voi_names": voi_names,
    }


def list_coordinates() -> List[str]:
    """List all the available coordinates (VOIs).

    Returns
    -------
    list of str
        A list with all available coordinates names.

    """
    return sorted(_available_coordinates.keys())


def get_coordinates(
    coords: str,
    target_data: Dict[str, Any],
    extra_input: Optional[Dict[str, Any]] = None,
) -> Tuple[ArrayLike, List[str]]:
    """Get coordinates, tailored for the target image.

    Parameters
    ----------
    coords : str
        The name of the coordinates.
    target_data : dict
        The corresponding item of the data object to which the coordinates
        will be applied.
    extra_input : dict, optional
        The other fields in the data object. Useful for accessing other data
        kinds that needs to be used in the computation of coordinates
        (default None).

    Returns
    -------
    numpy.ndarray
        The coordinates.
    list of str
        The names of the VOIs.

    Raises
    ------
    ValueError
        If ``extra_input`` is None when ``target_data``'s space is not MNI.

    """
    # Load the coordinates
    seeds, labels = load_coordinates(name=coords)

    return seeds, labels


def load_coordinates(name: str) -> Tuple[ArrayLike, List[str]]:
    """Load coordinates.

    Parameters
    ----------
    name : str
        The name of the coordinates.

    Returns
    -------
    numpy.ndarray
        The coordinates.
    list of str
        The names of the VOIs.

    Raises
    ------
    ValueError
        If ``name`` is invalid.

    Warns
    -----
    DeprecationWarning
        If ``Power`` is provided as the ``name``.

    """
    # Check for valid coordinates name
    if name not in _available_coordinates:
        raise_error(
            f"Coordinates {name} not found. "
            f"Valid options are: {list_coordinates()}"
        )

    # Put up deprecation notice
    if name == "Power":
        warn_with_log(
            msg=(
                "`Power` has been replaced with `Power2011` and will be "
                "removed in the next release. For now, it's available for "
                "backward compatibility."
            ),
            category=DeprecationWarning,
        )

    # Load coordinates
    t_coord = _available_coordinates[name]
    if isinstance(t_coord, Path):
        # Load via pandas
        df_coords = pd.read_csv(t_coord, sep="\t", header=None)
        coords = df_coords.iloc[:, [0, 1, 2]].to_numpy()
        names = list(df_coords.iloc[:, [3]].values[:, 0])
    else:
        coords = t_coord["coords"]
        coords = typing.cast(ArrayLike, coords)
        names = t_coord["voi_names"]
        names = typing.cast(List[str], names)

    return coords, names
