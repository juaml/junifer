"""Provide functions for masks."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import typing
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)

import nibabel as nib
import numpy as np
from nilearn.datasets import fetch_icbm152_brain_gm_mask
from nilearn.image import resample_to_img
from nilearn.masking import (
    compute_background_mask,
    compute_brain_mask,
    compute_epi_mask,
    intersect_masks,
)

from ..pipeline import WorkDirManager
from ..utils import logger, raise_error, run_ext_cmd
from .utils import closest_resolution


if TYPE_CHECKING:
    from nibabel import Nifti1Image

# Path to the masks
_masks_path = Path(__file__).parent / "masks"


def _fetch_icbm152_brain_gm_mask(
    target_img: "Nifti1Image",
    **kwargs,
):
    """Fetch ICBM152 brain mask and resample.

    Parameters
    ----------
    target_img : nibabel.Nifti1Image
        The image to which the mask will be resampled.
    **kwargs : dict
        Keyword arguments to be passed to
        :func:`nilearn.datasets.fetch_icbm152_brain_gm_mask`.

    Returns
    -------
    nibabel.Nifti1Image
        The resampled mask.

    """
    mask = fetch_icbm152_brain_gm_mask(**kwargs)
    mask = resample_to_img(
        mask, target_img, interpolation="nearest", copy=True
    )
    return mask


# A dictionary containing all supported masks and their respective file or
# data.

# Each entry is a dictionary that must contain at least the following keys:
# * 'family': the mask's family name (e.g., 'Vickery-Patil', 'Callable')
# * 'space': the mask's space (e.g., 'MNI', 'inherit')

# The built-in masks are files that are shipped with the package in the
# data/masks directory. The user can also register their own masks.

# Callable masks should be functions that take at least one parameter:
# * `target_img`: the image to which the mask will be applied.
_available_masks: Dict[str, Dict[str, Any]] = {
    "GM_prob0.2": {"family": "Vickery-Patil", "space": "IXI549Space"},
    "GM_prob0.2_cortex": {
        "family": "Vickery-Patil",
        "space": "IXI549Space",
    },
    "compute_brain_mask": {
        "family": "Callable",
        "func": compute_brain_mask,
        "space": "inherit",
    },
    "compute_background_mask": {
        "family": "Callable",
        "func": compute_background_mask,
        "space": "inherit",
    },
    "compute_epi_mask": {
        "family": "Callable",
        "func": compute_epi_mask,
        "space": "inherit",
    },
    "fetch_icbm152_brain_gm_mask": {
        "family": "Callable",
        "func": _fetch_icbm152_brain_gm_mask,
        "space": "MNI152NLin2009aAsym",
    },
}


def register_mask(
    name: str,
    mask_path: Union[str, Path],
    space: str,
    overwrite: bool = False,
) -> None:
    """Register a custom user mask.

    Parameters
    ----------
    name : str
        The name of the mask.
    mask_path : str or pathlib.Path
        The path to the mask file.
    space : str
        The space of the mask.
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
                    f"Cannot overwrite {name} mask. It is a built-in mask."
                )
        else:
            raise_error(
                f"Mask {name} already registered. Set `overwrite=True` "
                "to update its value."
            )
    # Convert str to Path
    if not isinstance(mask_path, Path):
        mask_path = Path(mask_path)
    # Add user parcellation info
    _available_masks[name] = {
        "path": str(mask_path.absolute()),
        "family": "CustomUserMask",
        "space": space,
    }


def list_masks() -> List[str]:
    """List all the available masks.

    Returns
    -------
    list of str
        A list with all available masks names.

    """
    return sorted(_available_masks.keys())


def get_mask(  # noqa: C901
    masks: Union[str, Dict, List[Union[Dict, str]]],
    target_data: Dict[str, Any],
    extra_input: Optional[Dict[str, Any]] = None,
) -> "Nifti1Image":
    """Get mask, tailored for the target image.

    Parameters
    ----------
    masks : str, dict or list of dict or str
        The name of the mask, or the name of a callable mask and the parameters
        of the mask as a dictionary. Several masks can be passed as a list.
    target_data : dict
        The corresponding item of the data object to which the mask will be
        applied.
    extra_input : dict, optional
        The other fields in the data object. Useful for accessing other data
        kinds that needs to be used in the computation of masks (default None).

    Returns
    -------
    Nifti1Image
        The mask image.

    Raises
    ------
    RuntimeError
        If masks are in different spaces and they need to be intersected /
        unionized or
        if warp / transformation file extension is not ".mat" or ".h5".
    ValueError
        If extra key is provided in addition to mask name in ``masks`` or
        if no mask is provided or
        if ``masks = "inherit"`` but ``extra_input`` is None or ``mask_item``
        is None or ``mask_items``'s value is not in ``extra_input`` or
        if callable parameters are passed to non-callable mask or
        if multiple masks are provided and their spaces do not match or
        if parameters are passed to :func:`nilearn.masking.intersect_masks`
        when there is only one mask or
        if ``extra_input`` is None when ``target_data``'s space is native.

    """
    # Get the min of the voxels sizes and use it as the resolution
    target_img = target_data["data"]
    inherited_mask_item = target_data.get("mask_item", None)
    resolution = np.min(target_img.header.get_zooms()[:3])

    if not isinstance(masks, list):
        masks = [masks]

    # Check that dicts have only one key
    invalid_elements = [
        x for x in masks if isinstance(x, dict) and len(x) != 1
    ]
    if len(invalid_elements) > 0:
        raise_error(
            "Each of the masks dictionary must have only one key, "
            "the name of the mask. The following dictionaries are invalid: "
            f"{invalid_elements}"
        )

    # Check params for the intersection function
    intersect_params = {}
    true_masks = []
    for t_mask in masks:
        if isinstance(t_mask, dict):
            if "threshold" in t_mask:
                intersect_params["threshold"] = t_mask["threshold"]
                continue
            elif "connected" in t_mask:
                intersect_params["connected"] = t_mask["connected"]
                continue
        # All the other elements are masks
        true_masks.append(t_mask)

    if len(true_masks) == 0:
        raise_error("No mask was passed. At least one mask is required.")
    # Get all the masks
    all_masks = []
    all_spaces = []
    for t_mask in true_masks:
        if isinstance(t_mask, dict):
            mask_name = next(iter(t_mask.keys()))
            mask_params = t_mask[mask_name]
        else:
            mask_name = t_mask
            mask_params = None

        # If mask is being inherited from previous steps like preprocessing
        if mask_name == "inherit":
            # Requires extra input to be passed
            if extra_input is None:
                raise_error(
                    "Cannot inherit mask from another data item "
                    "because no extra data was passed."
                )
            # Missing inherited mask item
            if inherited_mask_item is None:
                raise_error(
                    "Cannot inherit mask from another data item "
                    "because no mask item was specified "
                    "(missing `mask_item` key in the data object)."
                )
            # Missing inherited mask item in extra input
            if inherited_mask_item not in extra_input:
                raise_error(
                    "Cannot inherit mask from another data item "
                    f"because the item ({inherited_mask_item}) does not exist."
                )
            mask_img = extra_input[inherited_mask_item]["data"]
            mask_space = target_data["space"]
        # Starting with new mask
        else:
            # Load mask
            mask_object, _, mask_space = load_mask(
                mask_name, path_only=False, resolution=resolution
            )
            # Replace mask space with target space if mask's space is inherit
            if mask_space == "inherit":
                mask_space = target_data["space"]
            # If mask is callable like from nilearn
            if callable(mask_object):
                if mask_params is None:
                    mask_params = {}
                mask_img = mask_object(target_img, **mask_params)
            # Mask is a Nifti1Image
            else:
                # Mask params provided
                if mask_params is not None:
                    # Unused params
                    raise_error(
                        "Cannot pass callable params to a non-callable mask."
                    )
                # Resample mask to target image
                mask_img = resample_to_img(
                    mask_object,
                    target_img,
                    interpolation="nearest",
                    copy=True,
                )
        all_spaces.append(mask_space)
        all_masks.append(mask_img)

    # Multiple masks, need intersection / union
    if len(all_masks) > 1:
        # Make a set of unique spaces
        unique_spaces = set(all_spaces)
        # Intersect / union of masks only if all masks are in the same space
        if len(unique_spaces) == 1:
            mask_img = intersect_masks(all_masks, **intersect_params)
            # Store the mask space for further checks
            mask_space = next(iter(unique_spaces))
        else:
            raise_error(
                msg=(
                    f"Masks are in different spaces: {unique_spaces}, "
                    "unable to merge."
                ),
                klass=RuntimeError,
            )
    # Single mask
    else:
        if len(intersect_params) > 0:
            # Yes, I'm this strict!
            raise_error(
                "Cannot pass parameters to the intersection function "
                "when there is only one mask."
            )
        mask_img = all_masks[0]
        mask_space = all_spaces[0]

    # Warp mask if target data is native and mask space is not native
    if target_data["space"] == "native" and target_data["space"] != mask_space:
        # Check for extra inputs
        if extra_input is None:
            raise_error(
                "No extra input provided, requires `Warp` and `T1w` "
                "data types in particular for transformation to "
                f"{target_data['space']} space for further computation."
            )

        # Create component-scoped tempdir
        tempdir = WorkDirManager().get_tempdir(prefix="masks")

        # Save mask image to a component-scoped tempfile
        prewarp_mask_path = tempdir / "prewarp_mask.nii.gz"
        nib.save(mask_img, prewarp_mask_path)

        # Create element-scoped tempdir so that warped mask is
        # available later as nibabel stores file path reference for
        # loading on computation
        element_tempdir = WorkDirManager().get_element_tempdir(prefix="masks")

        # Create an element-scoped tempfile for warped output
        warped_mask_path = element_tempdir / "mask_warped.nii.gz"

        # Check for warp file type to use correct tool
        warp_file_ext = extra_input["Warp"]["path"].suffix
        if warp_file_ext == ".mat":
            logger.debug("Using FSL for mask warping")
            # Set applywarp command
            applywarp_cmd = [
                "applywarp",
                "--interp=nn",
                f"-i {prewarp_mask_path.resolve()}",
                # use resampled reference
                f"-r {target_data['reference_path'].resolve()}",
                f"-w {extra_input['Warp']['path'].resolve()}",
                f"-o {warped_mask_path.resolve()}",
            ]
            # Call applywarp
            run_ext_cmd(name="applywarp", cmd=applywarp_cmd)

        elif warp_file_ext == ".h5":
            logger.debug("Using ANTs for mask warping")
            # Set antsApplyTransforms command
            apply_transforms_cmd = [
                "antsApplyTransforms",
                "-d 3",
                "-e 3",
                "-n 'GenericLabel[NearestNeighbor]'",
                f"-i {prewarp_mask_path.resolve()}",
                # use resampled reference
                f"-r {target_data['reference_path'].resolve()}",
                f"-t {extra_input['Warp']['path'].resolve()}",
                f"-o {warped_mask_path.resolve()}",
            ]
            # Call antsApplyTransforms
            run_ext_cmd(name="antsApplyTransforms", cmd=apply_transforms_cmd)

        else:
            raise_error(
                msg=(
                    "Unknown warp / transformation file extension: "
                    f"{warp_file_ext}"
                ),
                klass=RuntimeError,
            )

        # Load nifti
        mask_img = nib.load(warped_mask_path)

        # Delete tempdir
        WorkDirManager().delete_tempdir(tempdir)

    return mask_img  # type: ignore


def load_mask(
    name: str,
    resolution: Optional[float] = None,
    path_only: bool = False,
) -> Tuple[Optional[Union["Nifti1Image", Callable]], Optional[Path], str]:
    """Load a mask.

    Parameters
    ----------
    name : str
        The name of the mask. Check valid options by calling
        :func:`.list_masks`.
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
    str
        The space of the mask.

    Raises
    ------
    ValueError
        If the ``name`` is invalid of if the mask family is invalid.

    """
    # Check for valid mask name
    if name not in _available_masks:
        raise_error(
            f"Mask {name} not found. Valid options are: {list_masks()}"
        )

    # Copy mask definition to avoid edits in original object
    mask_definition = _available_masks[name].copy()
    t_family = mask_definition.pop("family")

    # Check if the mask family is custom or built-in
    mask_img = None
    if t_family == "CustomUserMask":
        mask_fname = Path(mask_definition["path"])
    elif t_family == "Vickery-Patil":
        mask_fname = _load_vickery_patil_mask(name, resolution)
    elif t_family == "Callable":
        mask_img = mask_definition["func"]
        mask_fname = None
    else:
        raise_error(f"I don't know about the {t_family} mask family.")

    # Load mask
    if mask_fname is not None:
        logger.info(f"Loading mask {mask_fname.absolute()!s}")
        if path_only is False:
            # Load via nibabel
            mask_img = nib.load(mask_fname)

    # Type-cast to remove error
    mask_img = typing.cast("Nifti1Image", mask_img)
    return mask_img, mask_fname, mask_definition["space"]


def _load_vickery_patil_mask(
    name: str,
    resolution: Optional[float] = None,
) -> Path:
    """Load Vickery-Patil mask.

    Parameters
    ----------
    name : {"GM_prob0.2", "GM_prob0.2_cortex"}
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

    Raises
    ------
    ValueError
        If ``name`` is invalid or if ``resolution`` is invalid for
        ``name = "GM_prob0.2"``.

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
                f"Cannot find a GM_prob0.2 mask of resolution {resolution}"
            )
    elif name == "GM_prob0.2_cortex":
        mask_fname = "GMprob0.2_cortex_3mm_NA_rm.nii.gz"
    else:
        raise_error(f"Cannot find a Vickery-Patil mask called {name}")

    # Set path for masks
    mask_fname = _masks_path / "vickery-patil" / mask_fname

    return mask_fname
