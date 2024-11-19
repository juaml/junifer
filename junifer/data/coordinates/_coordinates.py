"""Provide a class for centralized coordinates data registry."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike

from ...utils import logger, raise_error
from ...utils.singleton import Singleton
from ..pipeline_data_registry_base import BasePipelineDataRegistry
from ..utils import get_native_warper
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
        # Each entry in registry is a dictionary that must contain at least
        # the following keys:
        # * 'space': the coordinates' space (e.g., 'MNI')
        # The built-in coordinates are files that are shipped with the package
        # in the data/VOIs directory. The user can also register their own
        # coordinates, which will be stored as numpy arrays in the dictionary.
        # Make built-in and external dictionaries for validation later
        self._builtin = {}
        self._external = {}

        # Path to the metadata of the VOIs
        _vois_meta_path = Path(__file__).parent / "VOIs" / "meta"

        self._builtin = {
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
            "Power2011": {
                "path": _vois_meta_path / "Power2011_MNI_VOIs.txt",
                "space": "MNI",
            },
            "Dosenbach": {
                "path": _vois_meta_path / "Dosenbach2010_MNI_VOIs.txt",
                "space": "MNI",
            },
            "Power2013": {
                "path": _vois_meta_path / "Power2013_MNI_VOIs.tsv",
                "space": "MNI",
            },
            "AutobiographicalMemory": {
                "path": _vois_meta_path / "AutobiographicalMemory_VOIs.txt",
                "space": "MNI",
            },
        }

        # Set built-in to registry
        self._registry = self._builtin

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
            If the coordinates ``name`` is already registered and
            ``overwrite=False`` or
            if the coordinates ``name`` is a built-in coordinates or
            if the ``coordinates`` is not a 2D array or
            if coordinate value does not have 3 components or
            if the ``voi_names`` shape does not match the
            ``coordinates`` shape.
        TypeError
            If ``coordinates`` is not a ``numpy.ndarray``.

        """
        # Check for attempt of overwriting built-in coordinates
        if name in self._builtin:
            if isinstance(self._registry[name].get("path"), Path):
                raise_error(
                    f"Coordinates: {name} already registered as built-in "
                    "coordinates."
                )
            if overwrite:
                logger.info(f"Overwriting coordinates: {name}")
            else:
                raise_error(
                    f"Coordinates: {name} already registered. "
                    "Set `overwrite=True` to update its value."
                )

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

        """
        # Check for valid coordinates name
        if name not in self._registry:
            raise_error(
                f"Coordinates: {name} not found. "
                f"Valid options are: {self.list}"
            )
        # Load coordinates
        t_coord = self._registry[name]
        # Load data
        if isinstance(t_coord.get("path"), Path):
            logger.debug(f"Loading coordinates {t_coord['path'].absolute()!s}")
            # Load via pandas
            df_coords = pd.read_csv(t_coord["path"], sep="\t", header=None)
            # Convert dataframe to numpy ndarray
            coords = df_coords.iloc[:, [0, 1, 2]].to_numpy()
            # Get label names
            names = list(df_coords.iloc[:, [3]].values[:, 0])
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
