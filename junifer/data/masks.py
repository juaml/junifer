"""Provide functions for masks."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
    Callable,
)

import numpy as np

import nibabel as nib
from nilearn.masking import (
    compute_brain_mask,
    compute_background_mask,
    compute_epi_mask,
)
from nilearn.image import resample_to_img

from ..utils.logging import logger, raise_error
from .utils import closest_resolution


if TYPE_CHECKING:
    from nibabel import Nifti1Image

# Path to the VOIs
_masks_path = Path(__file__).parent / "masks"

"""
A dictionary containing all supported masks and their respective file or
data.

The built-in masks are files that are shipped with the package in the
data/masks directory. The user can also register their own masks.
"""
_available_masks: Dict[str, Dict[str, Any]] = {
    "GM_prob0.2": {"family": "Vickery-Patil"},
    "GM_prob0.2_cortex": {"family": "Vickery-Patil"},
    "compute_brain": {"family": "Callable", "func": compute_brain_mask},
    "compute_background": {
        "family": "Callable",
        "func": compute_background_mask,
    },
    "compute_epi": {"family": "Callable", "func": compute_epi_mask},
}


def register_mask(
    name: str,
    mask_path: Union[str, Path],
    overwrite: bool = False,
) -> None:
    """Register a custom user mask.

    Parameters
    ----------
    name : str
        The name of the mask.
    mask_path : str or pathlib.Path
        The path to the mask file.
    overwrite : bool, optional
        If True, overwrite an existing mask with the same name.
        Does not apply to built-in mask (default False).

    Raises
    ------
    ValueError
        If the mask name is already registered and overwrite is set to
        False or if the mask name is a built-in mask.
    """
    # Check for attempt of overwriting built-in parcellations
    if name in _available_masks:
        if overwrite is True:
            logger.info(f"Overwriting {name} mask")
            if _available_masks[name]["family"] != "CustomUserMask":
                raise_error(
                    f"Cannot overwrite {name} mask. " "It is a built-in mask."
                )
        else:
            raise_error(
                f"Mask {name} already registered. Set `overwrite=True`"
                "to update its value."
            )
    # Convert str to Path
    if not isinstance(mask_path, Path):
        mask_path = Path(mask_path)
    # Add user parcellation info
    _available_masks[name] = {
        "path": str(mask_path.absolute()),
        "family": "CustomUserMask",
    }


def list_masks() -> List[str]:
    """List all the available masks.

    Returns
    -------
    list of str
        A list with all available masks names.
    """
    return sorted(_available_masks.keys())


def get_mask(
    name: str,
    target_img: "Nifti1Image",
    callable_params: Optional[Dict[str, Any]] = None,
) -> "Nifti1Image":
    """Get mask, tailored for the target image.

    Parameters
    ----------
    name : str
        The name of the mask.
    target_img : Nifti1Image
        The image to which the mask will be applied.
    callable_params : dict, optional
        Parameters to pass to the callable mask function (default None).
    Returns
    -------
    Nifti1Image
        The mask image.
    """
    # Get the min of the voxels sizes and use it as the resolution
    resolution = np.min(target_img.header.get_zooms()[:3])
    mask_img, _ = load_mask(name, path_only=False, resolution=resolution)
    if callable(mask_img):
        if callable_params is None:
            callable_params = {}
        mask_img = mask_img(target_img, **callable_params)
    else:
        if callable_params is not None:
            raise_error(
                "Cannot pass callable_params to a non-callable mask."
            )
        mask_img = resample_to_img(
            mask_img,
            target_img,
            interpolation="nearest",
            copy=True,
        )

    return mask_img


def load_mask(
    name: str,
    resolution: Optional[float] = None,
    path_only: bool = False,
) -> Tuple[Optional[Union["Nifti1Image", Callable]], Optional[Path]]:
    """Load mask.

    Parameters
    ----------
    name : str
        The name of the mask.
    resolution : float, optional
        The desired resolution of the mask to load. If it is not
        available, the closest resolution will be loaded. Preferably, use a
        resolution higher than the desired one. By default, will load the
        highest one (default None).
    path_only : bool, optional
        If True, the mask image will not be loaded (default False).

    Returns
    -------
    Nifti1Image, Callable or None
        Loaded mask image.
    pathlib.Path or None
        File path to the mask image.
    """
    mask_img = None
    if name not in _available_masks:
        raise_error(
            f"Mask {name} not found. " f"Valid options are: {list_masks()}"
        )

    mask_definition = _available_masks[name].copy()
    t_family = mask_definition.pop("family")

    if t_family == "CustomUserMask":
        mask_fname = Path(mask_definition["path"])
    elif t_family == "Vickery-Patil":
        mask_fname = _load_vickery_patil_mask(name, resolution)
    elif t_family == "Callable":
        mask_img = mask_definition["func"]
        mask_fname = None
    else:
        raise_error(f"I don't know about the {t_family} mask family.")

    if mask_fname is not None:
        logger.info(f"Loading mask {mask_fname.absolute()}")
        if path_only is False:
            mask_img = nib.load(mask_fname)

    return mask_img, mask_fname


def _load_vickery_patil_mask(
    name: str,
    resolution: Optional[float] = None,
) -> Path:
    """Load Vickery-Patil mask.

    Parameters
    ----------
    name : str
        The name of the mask.
    resolution : float, optional
        The desired resolution of the mask to load. If it is not
        available, the closest resolution will be loaded. Preferably, use a
        resolution higher than the desired one. By default, will load the
        highest one (default None).

    Returns
    -------
    pathlib.Path
        File path to the mask image.
    """
    if name == "GM_prob0.2":
        available_resolutions = [1.5, 3.0]
        to_load = closest_resolution(resolution, available_resolutions)
        if to_load == 3.0:
            mask_fname = (
                "CAT12_IXI555_MNI152_TMP_GS_GMprob0.2_clean_3mm.nii.gz"
            )
        elif to_load == 1.5:
            mask_fname = "CAT12_IXI555_MNI152_TMP_GS_GMprob0.2_clean.nii.gz"
        else:
            raise_error(
                f"Cannot find a GM_prob0.2 mask for resolution {resolution}"
            )
    elif name == "GM_prob0.2_cortex":
        mask_fname = "GMprob0.2_cortex_3mm_NA_rm.nii.gz"
    else:
        raise_error(f"Cannot find a Vickery-Patil mask called {name}")
    mask_fname = _masks_path / "vickery-patil" / mask_fname

    return mask_fname
