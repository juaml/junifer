"""Provide a class for centralized maps data registry."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Union

import nibabel as nib
import nilearn.image as nimg
import numpy as np
from junifer_data import get

from ...utils import logger, raise_error
from ..pipeline_data_registry_base import BasePipelineDataRegistry
from ..utils import (
    JUNIFER_DATA_PARAMS,
    closest_resolution,
    get_dataset_path,
    get_native_warper,
)
from ._ants_maps_warper import ANTsMapsWarper
from ._fsl_maps_warper import FSLMapsWarper


if TYPE_CHECKING:
    from nibabel.nifti1 import Nifti1Image


__all__ = ["MapsRegistry"]


class MapsRegistry(BasePipelineDataRegistry):
    """Class for maps data registry.

    This class is a singleton and is used for managing available maps
    data in a centralized manner.

    """

    def __init__(self) -> None:
        """Initialize the class."""
        super().__init__()
        # Each entry in registry is a dictionary that must contain at least
        # the following keys:
        # * 'family': the maps' family name (e.g., 'Smith')
        # * 'space': the maps' space (e.g., 'MNI')
        # and can also have optional key(s):
        # * 'valid_resolutions': a list of valid resolutions for the
        # maps (e.g., [1, 2])
        # The built-in maps are files that are shipped with the
        # junifer-data dataset.
        # Make built-in and external dictionaries for validation later
        self._builtin = {}
        self._external = {}

        # Add Smith
        for comp in ["rsn", "bm"]:
            for dim in [10, 20, 70]:
                self._builtin.update(
                    {
                        f"Smith_{comp}_{dim}": {
                            "family": "Smith2009",
                            "components": comp,
                            "dimension": dim,
                            "space": "MNI152NLin6Asym",
                        }
                    }
                )

        # Update registry with built-in ones
        self._registry.update(self._builtin)

    def register(
        self,
        name: str,
        maps_path: Union[str, Path],
        maps_labels: list[str],
        space: str,
        overwrite: bool = False,
    ) -> None:
        """Register a custom user map(s).

        Parameters
        ----------
        name : str
            The name of the map(s).
        maps_path : str or pathlib.Path
            The path to the map(s) file.
        maps_labels : list of str
            The list of labels for the map(s).
        space : str
            The template space of the map(s), e.g., "MNI152NLin6Asym".
        overwrite : bool, optional
            If True, overwrite an existing maps with the same name.
            Does not apply to built-in maps (default False).

        Raises
        ------
        ValueError
            If the map(s) ``name`` is a built-in map(s) or
            if the map(s) ``name`` is already registered and
            ``overwrite=False``.

        """
        # Check for attempt of overwriting built-in maps
        if name in self._builtin:
            raise_error(
                f"Map(s): {name} already registered as built-in map(s)."
            )
        # Check for attempt of overwriting external maps
        if name in self._external:
            if overwrite:
                logger.info(f"Overwriting map(s): {name}")
            else:
                raise_error(
                    f"Map(s): {name} already registered. Set "
                    "`overwrite=True` to update its value."
                )
        # Convert str to Path
        if not isinstance(maps_path, Path):
            maps_path = Path(maps_path)
        # Registration
        logger.info(f"Registering map(s): {name}")
        # Add user maps info
        self._external[name] = {
            "path": maps_path,
            "labels": maps_labels,
            "family": "CustomUserMaps",
            "space": space,
        }
        # Update registry
        self._registry[name] = {
            "path": maps_path,
            "labels": maps_labels,
            "family": "CustomUserMaps",
            "space": space,
        }

    def deregister(self, name: str) -> None:
        """De-register a custom user map(s).

        Parameters
        ----------
        name : str
            The name of the map(s).

        """
        logger.info(f"De-registering map(s): {name}")
        # Remove maps info
        _ = self._external.pop(name)
        # Update registry
        _ = self._registry.pop(name)

    def load(
        self,
        name: str,
        target_space: str,
        resolution: Optional[float] = None,
        path_only: bool = False,
    ) -> tuple[Optional["Nifti1Image"], list[str], Path, str]:
        """Load map(s) and labels.

        Parameters
        ----------
        name : str
            The name of the map(s).
        target_space : str
            The desired space of the map(s).
        resolution : float, optional
            The desired resolution of the map(s) to load. If it is not
            available, the closest resolution will be loaded. Preferably, use a
            resolution higher than the desired one. By default, will load the
            highest one (default None).
        path_only : bool, optional
            If True, the map(s) image will not be loaded (default False).

        Returns
        -------
        Nifti1Image or None
            Loaded map(s) image.
        list of str
            Map(s) labels.
        pathlib.Path
            File path to the map(s) image.
        str
            The space of the map(s).

        Raises
        ------
        ValueError
            If ``name`` is invalid or
            if the map(s) family is invalid or
            if the map(s) values and labels
            don't have equal dimension or if the value range is invalid.

        """
        # Check for valid maps name
        if name not in self._registry:
            raise_error(
                f"Map(s): {name} not found. Valid options are: {self.list}"
            )

        # Copy maps definition to avoid edits in original object
        maps_def = self._registry[name].copy()
        t_family = maps_def.pop("family")
        space = maps_def.pop("space")

        # Check and get highest resolution
        if space != target_space:
            logger.info(
                f"Map(s) will be warped from {space} to {target_space} "
                "using highest resolution"
            )
            resolution = None

        # Check if the maps family is custom or built-in
        if t_family == "CustomUserMaps":
            maps_fname = maps_def["path"]
            maps_labels = maps_def["labels"]
        elif t_family in [
            "Smith2009",
        ]:
            # Load maps and labels
            if t_family == "Smith2009":
                maps_fname, maps_labels = _retrieve_smith(
                    resolution=resolution,
                    **maps_def,
                )
        else:  # pragma: no cover
            raise_error(f"Unknown map(s) family: {t_family}")

        # Load maps image and values
        logger.info(f"Loading map(s): {maps_fname.absolute()!s}")
        maps_img = None
        if not path_only:
            # Load image via nibabel
            maps_img = nib.load(maps_fname)
            # Get regions
            maps_regions = maps_img.get_fdata().shape[-1]
            # Check for dimension
            if maps_regions != len(maps_labels):
                raise_error(
                    f"Map(s) {name} has {maps_regions} "
                    f"regions but {len(maps_labels)} labels."
                )

        return maps_img, maps_labels, maps_fname, space

    def get(
        self,
        maps: str,
        target_data: dict[str, Any],
        extra_input: Optional[dict[str, Any]] = None,
    ) -> tuple["Nifti1Image", list[str]]:
        """Get map(s), tailored for the target image.

        Parameters
        ----------
        maps : str
            The name of the map(s).
        target_data : dict
            The corresponding item of the data object to which the map(s)
            will be applied.
        extra_input : dict, optional
            The other fields in the data object. Useful for accessing other
            data kinds that needs to be used in the computation of
            map(s) (default None).

        Returns
        -------
        Nifti1Image
            The map(s) image.
        list of str
            Map(s) labels.

        Raises
        ------
        ValueError
            If ``extra_input`` is None when ``target_data``'s space is native.

        """
        # Check pre-requirements for space manipulation
        target_space = target_data["space"]
        logger.debug(f"Getting {maps} in {target_space} space.")
        # Extra data type requirement check if target space is native
        if target_space == "native":  # pragma: no cover
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
            # Set target standard space to warp file space source
            target_std_space = warper_spec["src"]
            logger.debug(
                f"Target space is native. Will warp from {target_std_space}"
            )
        else:
            # Set target standard space to target space
            target_std_space = target_space

        # Get the min of the voxels sizes and use it as the resolution
        target_img = target_data["data"]
        resolution = np.min(target_img.header.get_zooms()[:3])

        # Load maps
        logger.debug(f"Loading map(s) {maps}")
        img, labels, _, space = self.load(
            name=maps,
            resolution=resolution,
            target_space=target_space,
        )

        # Convert maps spaces if required;
        # cannot be "native" due to earlier check
        if space != target_std_space:
            logger.debug(
                f"Warping {maps} to {target_std_space} space using ANTs."
            )
            raw_img = ANTsMapsWarper().warp(
                maps_name=maps,
                maps_img=img,
                src=space,
                dst=target_std_space,
                target_data=target_data,
                warp_data=None,
            )
            # Remove extra dimension added by ANTs
            img = nimg.math_img("np.squeeze(img)", img=raw_img)

        if target_space != "native":
            # No warping is going to happen, just resampling, because
            # we are in the correct space
            logger.debug(f"Resampling {maps} to target image.")
            # Resample maps to target image
            img = nimg.resample_to_img(
                source_img=img,
                target_img=target_img,
                interpolation="continuous",
                copy=True,
            )
        else:  # pragma: no cover
            # Warp maps if target space is native as either
            # the image is in the right non-native space or it's
            # warped from one non-native space to another non-native space
            logger.debug(
                "Warping map(s) to native space using "
                f"{warper_spec['warper']}."
            )
            # extra_input check done earlier and warper_spec exists
            if warper_spec["warper"] == "fsl":
                img = FSLMapsWarper().warp(
                    maps_name="native",
                    maps_img=img,
                    target_data=target_data,
                    warp_data=warper_spec,
                )
            elif warper_spec["warper"] == "ants":
                img = ANTsMapsWarper().warp(
                    maps_name="native",
                    maps_img=img,
                    src="",
                    dst="native",
                    target_data=target_data,
                    warp_data=warper_spec,
                )

        return img, labels


def _retrieve_smith(
    resolution: Optional[float] = None,
    components: Optional[str] = None,
    dimension: Optional[int] = None,
) -> tuple[Path, list[str]]:
    """Retrieve Smith maps.

    Parameters
    ----------
    resolution : 2.0, optional
        The desired resolution of the maps to load. If it is not
        available, the closest resolution will be loaded. Preferably, use a
        resolution higher than the desired one. By default, will load the
        highest one (default None). Available resolution for these
        maps are 2mm.
    components : {"rsn", "bm"}, optional
        The components to load. "rsn" loads the resting-fMRI components and
        "bm" loads the BrainMap components (default None).
    dimension : {10, 20, 70}, optional
        The number of dimensions to load (default None).

    Returns
    -------
    pathlib.Path
        File path to the maps image.
    list of str
        Maps labels.

    Raises
    ------
    ValueError
        If invalid value is provided for ``components`` or ``dimension``.

    """
    logger.info("Maps parameters:")
    logger.info(f"\tresolution: {resolution}")
    logger.info(f"\tcomponents: {components}")
    logger.info(f"\tdimension: {dimension}")

    # Check resolution
    _valid_resolutions = [2.0]
    resolution = closest_resolution(resolution, _valid_resolutions)

    # Check components value
    _valid_components = ["rsn", "bm"]
    if components not in _valid_components:
        raise_error(
            f"The parameter `components` ({components}) needs to be one of "
            f"the following: {_valid_components}"
        )

    # Check dimension value
    _valid_dimension = [10, 20, 70]
    if dimension not in _valid_dimension:
        raise_error(
            f"The parameter `dimension` ({dimension}) needs to be one of the "
            f"following: {_valid_dimension}"
        )

    # Fetch file path
    maps_img_path = get(
        file_path=Path(
            f"parcellations/Smith2009/{components}{dimension}.nii.gz"
        ),
        dataset_path=get_dataset_path(),
        **JUNIFER_DATA_PARAMS,
    )

    return maps_img_path, [f"Map_{i}" for i in range(dimension)]
