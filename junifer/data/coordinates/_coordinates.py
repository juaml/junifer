"""Provide a class for centralized coordinates data registry."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd
from junifer_data import get
from numpy.typing import ArrayLike

from ...utils import logger, raise_error
from ...utils.singleton import Singleton
from ..pipeline_data_registry_base import BasePipelineDataRegistry
from ..utils import JUNIFER_DATA_PARAMS, get_dataset_path, get_native_warper
from ._ants_coordinates_warper import ANTsCoordinatesWarper
from ._fsl_coordinates_warper import FSLCoordinatesWarper


__all__ = ["CoordinatesRegistry"]


class CoordinatesRegistry(BasePipelineDataRegistry, metaclass=Singleton):
    """Class for coordinates data registry.

    This class is a singleton and is used for managing available coordinates
    data in a centralized manner.

    """

    def __init__(self) -> None:
        """Initialize the class."""
        super().__init__()
        # Each entry in registry is a dictionary that must contain at least
        # the following keys:
        # * 'space': the coordinates' space (e.g., 'MNI')
        # The built-in coordinates are files that are shipped with the
        # junifer-data dataset. The user can also register their own
        # coordinates, which will be stored as numpy arrays in the dictionary.
        # Make built-in and external dictionaries for validation later
        self._builtin = {}
        self._external = {}

        self._builtin.update(
            {
                "CogAC": {
                    "file_path_suffix": "CogAC/CogAC_VOIs.txt",
                    "space": "MNI",
                },
                "CogAR": {
                    "file_path_suffix": "CogAR/CogAR_VOIs.txt",
                    "space": "MNI",
                },
                "DMNBuckner": {
                    "file_path_suffix": "DMNBuckner/DMNBuckner_VOIs.txt",
                    "space": "MNI",
                },
                "eMDN": {
                    "file_path_suffix": "eMDN/eMDN_VOIs.txt",
                    "space": "MNI",
                },
                "Empathy": {
                    "file_path_suffix": "Empathy/Empathy_VOIs.txt",
                    "space": "MNI",
                },
                "eSAD": {
                    "file_path_suffix": "eSAD/eSAD_VOIs.txt",
                    "space": "MNI",
                },
                "extDMN": {
                    "file_path_suffix": "extDMN/extDMN_VOIs.txt",
                    "space": "MNI",
                },
                "Motor": {
                    "file_path_suffix": "Motor/Motor_VOIs.txt",
                    "space": "MNI",
                },
                "MultiTask": {
                    "file_path_suffix": "MultiTask/MultiTask_VOIs.txt",
                    "space": "MNI",
                },
                "PhysioStress": {
                    "file_path_suffix": "PhysioStress/PhysioStress_VOIs.txt",
                    "space": "MNI",
                },
                "Rew": {
                    "file_path_suffix": "Rew/Rew_VOIs.txt",
                    "space": "MNI",
                },
                "Somatosensory": {
                    "file_path_suffix": "Somatosensory/Somatosensory_VOIs.txt",
                    "space": "MNI",
                },
                "ToM": {
                    "file_path_suffix": "ToM/ToM_VOIs.txt",
                    "space": "MNI",
                },
                "VigAtt": {
                    "file_path_suffix": "VigAtt/VigAtt_VOIs.txt",
                    "space": "MNI",
                },
                "WM": {
                    "file_path_suffix": "WM/WM_VOIs.txt",
                    "space": "MNI",
                },
                "Power2011": {
                    "file_path_suffix": "Power/Power2011_MNI_VOIs.txt",
                    "space": "MNI",
                },
                "Dosenbach": {
                    "file_path_suffix": "Dosenbach/Dosenbach2010_MNI_VOIs.txt",
                    "space": "MNI",
                },
                "AutobiographicalMemory": {
                    "file_path_suffix": (
                        "AutobiographicalMemory/AutobiographicalMemory_VOIs.txt"
                    ),
                    "space": "MNI",
                },
                "Seitzman2018": {
                    "file_path_suffix": "Seitzman/Seitzman2018_MNI_VOIs.txt",
                    "space": "MNI",
                },
            }
        )

        # Update registry with built-in ones
        self._registry.update(self._builtin)

    def register(
        self,
        name: str,
        coordinates: ArrayLike,
        voi_names: list[str],
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
            columns. Each row corresponds to a volume-of-interest (VOI) and
            each column corresponds to a spatial dimension (i.e. x, y, and
            z-coordinates).
        voi_names : list of str
            The names of the VOIs.
        space : str
            The space of the coordinates, e.g., "MNI".
        overwrite : bool, optional
            If True, overwrite an existing list of coordinates with the same
            name. Does not apply to built-in coordinates (default False).

        Raises
        ------
        ValueError
            If the coordinates ``name`` is a built-in coordinates or
            if the coordinates ``name`` is already registered and
            ``overwrite=False`` or
            if the ``coordinates`` is not a 2D array or
            if coordinate value does not have 3 components or
            if the ``voi_names`` shape does not match the
            ``coordinates`` shape.
        TypeError
            If ``coordinates`` is not a ``numpy.ndarray``.

        """
        # Check for attempt of overwriting built-in coordinates
        if name in self._builtin:
            raise_error(
                f"Coordinates: {name} already registered as built-in "
                "coordinates."
            )
        # Check for attempt of overwriting external coordinates
        if name in self._external:
            if overwrite:
                logger.info(f"Overwriting coordinates: {name}")
            else:
                raise_error(
                    f"Coordinates: {name} already registered. "
                    "Set `overwrite=True` to update its value."
                )
        # Further checks
        if not isinstance(coordinates, np.ndarray):
            raise_error(
                "Coordinates must be a `numpy.ndarray`, "
                f"not {type(coordinates)}.",
                klass=TypeError,
            )
        if coordinates.ndim != 2:
            raise_error(
                f"Coordinates must be a 2D array, not {coordinates.ndim}D."
            )
        if coordinates.shape[1] != 3:
            raise_error(
                "Each coordinate must have 3 values, "
                f"not {coordinates.shape[1]}"
            )
        if len(voi_names) != coordinates.shape[0]:
            raise_error(
                f"Length of `voi_names` ({len(voi_names)}) does not match the "
                f"number of `coordinates` ({coordinates.shape[0]})."
            )
        # Registration
        logger.info(f"Registering coordinates: {name}")
        # Add coordinates info
        self._external[name] = {
            "coords": coordinates,
            "voi_names": voi_names,
            "space": space,
        }
        # Update registry
        self._registry[name] = {
            "coords": coordinates,
            "voi_names": voi_names,
            "space": space,
        }

    def deregister(self, name: str) -> None:
        """De-register a custom user coordinates.

        Parameters
        ----------
        name : str
            The name of the coordinates.

        """
        logger.info(f"De-registering coordinates: {name}")
        # Remove coordinates info
        _ = self._external.pop(name)
        # Update registry
        _ = self._registry.pop(name)

    def load(self, name: str) -> tuple[ArrayLike, list[str], str]:
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
        RuntimeError
            If there is a problem fetching the coordinates file.

        """
        # Check for valid coordinates name
        if name not in self._registry:
            raise_error(
                f"Coordinates: {name} not found. "
                f"Valid options are: {self.list}"
            )
        # Load coordinates info
        t_coord = self._registry[name]

        # Load data for in-built ones
        if t_coord.get("file_path_suffix") is not None:
            # Set file path to retrieve
            coords_file_path = Path(
                f"coordinates/{t_coord['file_path_suffix']}"
            )
            logger.debug(f"Loading coordinates: `{name}`")
            # Load via pandas
            df_coords = pd.read_csv(
                get(
                    file_path=coords_file_path,
                    dataset_path=get_dataset_path(),
                    **JUNIFER_DATA_PARAMS,
                ),
                sep="\t",
                header=None,
            )
            # Convert dataframe to numpy ndarray
            coords = df_coords.iloc[:, [0, 1, 2]].to_numpy()
            # Get label names
            names = list(df_coords.iloc[:, [3]].values[:, 0])
        # Load data for external ones
        else:
            coords = t_coord["coords"]
            names = t_coord["voi_names"]

        return coords, names, t_coord["space"]

    def get(
        self,
        coords: str,
        target_data: dict[str, Any],
        extra_input: Optional[dict[str, Any]] = None,
    ) -> tuple[ArrayLike, list[str]]:
        """Get coordinates, tailored for the target data.

        Parameters
        ----------
        coords : str
            The name of the coordinates.
        target_data : dict
            The corresponding item of the data object to which the coordinates
            will be applied.
        extra_input : dict, optional
            The other fields in the data object. Useful for accessing other
            data kinds that needs to be used in the computation of coordinates
            (default None).

        Returns
        -------
        numpy.ndarray
            The coordinates.
        list of str
            The names of the VOIs.

        Raises
        ------
        RuntimeError
            If warping specification required for warping using ANTs, is not
            found.
        ValueError
            If ``extra_input`` is None when ``target_data``'s space is native.

        """
        # Load the coordinates
        seeds, labels, _ = self.load(name=coords)

        # Transform coordinate if target data is native
        if target_data["space"] == "native":
            # Check for extra inputs
            if extra_input is None:
                raise_error(
                    "No extra input provided, requires `Warp` and `T1w` "
                    "data types in particular for transformation to "
                    f"{target_data['space']} space for further computation."
                )

            # Get native space warper spec
            warper_spec = get_native_warper(
                target_data=target_data,
                other_data=extra_input,
            )
            # Conditional for warping tool implementation
            if warper_spec["warper"] == "fsl":
                seeds = FSLCoordinatesWarper().warp(
                    seeds=seeds,
                    target_data=target_data,
                    warp_data=warper_spec,
                )
            elif warper_spec["warper"] == "ants":
                # Requires the inverse warp
                inverse_warper_spec = get_native_warper(
                    target_data=target_data,
                    other_data=extra_input,
                    inverse=True,
                )
                # Check warper
                if inverse_warper_spec["warper"] != "ants":
                    raise_error(
                        klass=RuntimeError,
                        msg=(
                            "Warping specification mismatch for native space "
                            "warping of coordinates using ANTs."
                        ),
                    )
                seeds = ANTsCoordinatesWarper().warp(
                    seeds=seeds,
                    target_data=target_data,
                    warp_data=inverse_warper_spec,
                )

        return seeds, labels
