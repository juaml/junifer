"""Provide functions for list of coordinates."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import subprocess
import typing
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike

from ..pipeline import WorkDirManager
from ..utils.logging import logger, raise_error, warn_with_log


# Path to the VOIs
_vois_path = Path(__file__).parent / "VOIs"

# Path to the metadata of the VOIs
_vois_meta_path = _vois_path / "meta"

# A dictionary containing all supported coordinates and their respective file
# or data.

# Each entry is a dictionary that must contain at least the following keys:
# * 'space': the coordinates' space (e.g., 'MNI')

# The built-in coordinates are files that are shipped with the package in the
# data/VOIs directory. The user can also register their own coordinates, which
# will be stored as numpy arrays in the dictionary.
_available_coordinates: Dict[
    str, Dict[str, Union[Path, ArrayLike, List[str]]]
] = {
    "CogAC": {
        "path": _vois_meta_path / "CogAC_VOIs.txt",
        "space": "MNI",
    },
    "CogAR": {
        "path": _vois_meta_path / "CogAR_VOIs.txt",
        "space": "MNI",
    },
    "DMNBuckner": {
        "path": _vois_meta_path / "DMNBuckner_VOIs.txt",
        "space": "MNI",
    },
    "eMDN": {
        "path": _vois_meta_path / "eMDN_VOIs.txt",
        "space": "MNI",
    },
    "Empathy": {
        "path": _vois_meta_path / "Empathy_VOIs.txt",
        "space": "MNI",
    },
    "eSAD": {
        "path": _vois_meta_path / "eSAD_VOIs.txt",
        "space": "MNI",
    },
    "extDMN": {
        "path": _vois_meta_path / "extDMN_VOIs.txt",
        "space": "MNI",
    },
    "Motor": {
        "path": _vois_meta_path / "Motor_VOIs.txt",
        "space": "MNI",
    },
    "MultiTask": {
        "path": _vois_meta_path / "MultiTask_VOIs.txt",
        "space": "MNI",
    },
    "PhysioStress": {
        "path": _vois_meta_path / "PhysioStress_VOIs.txt",
        "space": "MNI",
    },
    "Rew": {
        "path": _vois_meta_path / "Rew_VOIs.txt",
        "space": "MNI",
    },
    "Somatosensory": {
        "path": _vois_meta_path / "Somatosensory_VOIs.txt",
        "space": "MNI",
    },
    "ToM": {
        "path": _vois_meta_path / "ToM_VOIs.txt",
        "space": "MNI",
    },
    "VigAtt": {
        "path": _vois_meta_path / "VigAtt_VOIs.txt",
        "space": "MNI",
    },
    "WM": {
        "path": _vois_meta_path / "WM_VOIs.txt",
        "space": "MNI",
    },
    "Power": {
        "path": _vois_meta_path / "Power2011_MNI_VOIs.txt",
        "space": "MNI",
    },
    "Dosenbach": {
        "path": _vois_meta_path / "Dosenbach2010_MNI_VOIs.txt",
        "space": "MNI",
    },
}


def register_coordinates(
    name: str,
    coordinates: ArrayLike,
    voi_names: List[str],
    space: str,
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
    space : str
        The space of the coordinates.
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
        if isinstance(_available_coordinates[name].get("path"), Path):
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
        "space": space,
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
        If ``extra_input`` is None when ``target_data``'s space is native.

    """
    # Load the coordinates
    seeds, labels, _ = load_coordinates(name=coords)

    # Transform coordinate if target data is native
    if target_data["space"] == "native":
        # Check for extra inputs
        if extra_input is None:
            raise_error(
                "No extra input provided, requires `Warp` and `T1w` "
                "data types in particular for transformation to "
                f"{target_data['space']} space for further computation."
            )

        # Create component-scoped tempdir
        tempdir = WorkDirManager().get_tempdir(prefix="coordinates")

        # Save existing coordinates to a component-scoped tempfile
        pretransform_coordinates_path = (
            tempdir / "pretransform_coordinates.txt"
        )
        np.savetxt(pretransform_coordinates_path, seeds)

        # Create element-scoped tempdir so that transformed coordinates is
        # available later as numpy stores file path reference for
        # loading on computation
        element_tempdir = WorkDirManager().get_element_tempdir(
            prefix="coordinates"
        )

        # Create an element-scoped tempfile for transformed coordinates output
        img2imgcoord_out_path = element_tempdir / "coordinates_transformed.txt"
        # Set img2imgcoord command
        img2imgcoord_cmd = [
            "cat",
            f"{pretransform_coordinates_path.resolve()}",
            "| img2imgcoord -mm",
            f"-src {target_data['path'].resolve()}",
            f"-dest {target_data['reference_path'].resolve()}",
            f"-warp {extra_input['Warp']['path'].resolve()}",
            f"> {img2imgcoord_out_path.resolve()};",
            f"sed -i 1d {img2imgcoord_out_path.resolve()}",
        ]
        # Call img2imgcoord
        img2imgcoord_cmd_str = " ".join(img2imgcoord_cmd)
        logger.info(
            f"img2imgcoord command to be executed: {img2imgcoord_cmd_str}"
        )
        img2imgcoord_process = subprocess.run(
            img2imgcoord_cmd_str,  # string needed with shell=True
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,  # needed for respecting $PATH
            check=False,
        )
        # Check for success or failure
        if img2imgcoord_process.returncode == 0:
            logger.info(
                "img2imgcoord succeeded with the following output: "
                f"{img2imgcoord_process.stdout}"
            )
        else:
            raise_error(
                msg="img2imgcoord failed with the following error: "
                f"{img2imgcoord_process.stdout}",
                klass=RuntimeError,
            )

        # Load coordinates
        seeds = np.loadtxt(img2imgcoord_out_path)

        # Delete tempdir
        WorkDirManager().delete_tempdir(tempdir)

    return seeds, labels


def load_coordinates(name: str) -> Tuple[ArrayLike, List[str], str]:
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
    str
        The space of the coordinates.

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
    if isinstance(t_coord.get("path"), Path):
        # Load via pandas
        df_coords = pd.read_csv(t_coord["path"], sep="\t", header=None)
        coords = df_coords.iloc[:, [0, 1, 2]].to_numpy()
        names = list(df_coords.iloc[:, [3]].values[:, 0])
    else:
        coords = t_coord["coords"]
        coords = typing.cast(ArrayLike, coords)
        names = t_coord["voi_names"]
        names = typing.cast(List[str], names)

    return coords, names, t_coord["space"]
