"""Functions for mask manipulation."""

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
from nilearn.image import get_data, new_img_like, resample_to_img
from nilearn.masking import (
    compute_background_mask,
    compute_epi_mask,
    intersect_masks,
)

from ..pipeline import WorkDirManager
from ..utils import logger, raise_error, run_ext_cmd
from .template_spaces import get_template, get_xfm
from .utils import closest_resolution


if TYPE_CHECKING:
    from nibabel import Nifti1Image


__all__ = [
    "compute_brain_mask",
    "register_mask",
    "list_masks",
    "get_mask",
    "load_mask",
]


# Path to the masks
_masks_path = Path(__file__).parent / "masks"


def compute_brain_mask(
    target_data: Dict[str, Any],
    extra_input: Optional[Dict[str, Any]] = None,
    mask_type: str = "brain",
    threshold: float = 0.5,
) -> "Nifti1Image":
    """Compute the whole-brain, grey-matter or white-matter mask.

    This mask is calculated using the template space and resolution as found
    in the ``target_data``.

    Parameters
    ----------
    target_data : dict
        The corresponding item of the data object for which mask will be
        loaded.
    extra_input : dict, optional
        The other fields in the data object. Useful for accessing other data
        types (default None).
    mask_type : {"brain", "gm", "wm"}, optional
        Type of mask to be computed:

        * "brain" : whole-brain mask
        * "gm" : grey-matter mask
        * "wm" : white-matter mask

        (default "brain").
    threshold : float, optional
        The value under which the template is cut off (default 0.5).

    Returns
    -------
    Nifti1Image
        The mask (3D image).

    Raises
    ------
    ValueError
        If ``mask_type`` is invalid or
        if ``extra_input`` is None when ``target_data``'s space is native.

    """
    logger.debug(f"Computing {mask_type} mask")

    if mask_type not in ["brain", "gm", "wm"]:
        raise_error(f"Unknown mask type: {mask_type}")

    # Check pre-requirements for space manipulation
    target_space = target_data["space"]
    # Set target standard space to target space
    target_std_space = target_space
    # Extra data type requirement check if target space is native
    if target_space == "native":
        # Check for extra inputs
        if extra_input is None:
            raise_error(
                "No extra input provided, requires `Warp` "
                "data type to infer target template space."
            )
        # Set target standard space to warp file space source
        target_std_space = extra_input["Warp"]["src"]

    # Fetch template in closest resolution
    template = get_template(
        space=target_std_space,
        target_data=target_data,
        extra_input=extra_input,
        template_type=mask_type if mask_type in ["gm", "wm"] else "T1w",
    )
    # Resample template to target image
    target_img = target_data["data"]
    resampled_template = resample_to_img(
        source_img=template, target_img=target_img
    )

    # Threshold and get mask
    mask = (get_data(resampled_template) >= threshold).astype("int8")

    return new_img_like(target_img, mask)  # type: ignore


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
    "UKB_15K_GM": {
        "family": "UKB",
        "space": "MNI152NLin6Asym",
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
        The space of the mask, for e.g., "MNI152NLin6Asym".
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
        If warp / transformation file extension is not ".mat" or ".h5".
    ValueError
        If extra key is provided in addition to mask name in ``masks`` or
        if no mask is provided or
        if ``masks = "inherit"`` and ``mask`` key for the ``target_data`` is
        not found or
        if callable parameters are passed to non-callable mask or
        if parameters are passed to :func:`nilearn.masking.intersect_masks`
        when there is only one mask or
        if ``extra_input`` is None when ``target_data``'s space is native.

    """
    # Check pre-requirements for space manipulation
    target_space = target_data["space"]
    # Set target standard space to target space
    target_std_space = target_space
    # Extra data type requirement check if target space is native
    if target_space == "native":
        # Check for extra inputs
        if extra_input is None:
            raise_error(
                "No extra input provided, requires `Warp` and `T1w` "
                "data types in particular for transformation to "
                f"{target_data['space']} space for further computation."
            )
        # Set target standard space to warp file space source
        target_std_space = extra_input["Warp"]["src"]

    # Get the min of the voxels sizes and use it as the resolution
    target_img = target_data["data"]
    resolution = np.min(target_img.header.get_zooms()[:3])

    # Convert masks to list if not already
    if not isinstance(masks, list):
        masks = [masks]

    # Check that masks passed as dicts have only one key
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

    # Get the nested mask data type for the input data type
    inherited_mask_item = target_data.get("mask", None)

    # Create component-scoped tempdir
    tempdir = WorkDirManager().get_tempdir(prefix="masks")
    # Create element-scoped tempdir so that warped mask is
    # available later as nibabel stores file path reference for
    # loading on computation
    element_tempdir = WorkDirManager().get_element_tempdir(prefix="masks")

    # Get all the masks
    all_masks = []
    for t_mask in true_masks:
        if isinstance(t_mask, dict):
            mask_name = next(iter(t_mask.keys()))
            mask_params = t_mask[mask_name]
        else:
            mask_name = t_mask
            mask_params = None

        # If mask is being inherited from the datagrabber or a preprocessor,
        # check that it's accessible
        if mask_name == "inherit":
            if inherited_mask_item is None:
                raise_error(
                    "Cannot inherit mask from the target data. Either the "
                    "DataGrabber or a Preprocessor does not provide `mask` "
                    "for the target data type."
                )
            mask_img = inherited_mask_item["data"]
        # Starting with new mask
        else:
            # Load mask
            mask_object, _, mask_space = load_mask(
                mask_name, path_only=False, resolution=resolution
            )
            # Replace mask space with target space if mask's space is inherit
            if mask_space == "inherit":
                mask_space = target_std_space
            # If mask is callable like from nilearn
            if callable(mask_object):
                if mask_params is None:
                    mask_params = {}
                # From nilearn
                if mask_name != "compute_brain_mask":
                    mask_img = mask_object(target_img, **mask_params)
                # Not from nilearn
                else:
                    mask_img = mask_object(target_data, **mask_params)
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
                    source_img=mask_object,
                    target_img=target_img,
                    interpolation="nearest",
                    copy=True,
                )
            # Convert mask space if required
            if mask_space != target_std_space:
                # Get xfm file
                xfm_file_path = get_xfm(src=mask_space, dst=target_std_space)
                # Get target standard space template
                target_std_space_template_img = get_template(
                    space=target_std_space,
                    target_data=target_data,
                    extra_input=extra_input,
                )

                # Save mask image to a component-scoped tempfile
                mask_path = tempdir / f"{mask_name}.nii.gz"
                nib.save(mask_img, mask_path)

                # Save template
                target_std_space_template_path = (
                    tempdir / f"{target_std_space}_T1w_{resolution}.nii.gz"
                )
                nib.save(
                    target_std_space_template_img,
                    target_std_space_template_path,
                )

                # Set warped mask path
                warped_mask_path = element_tempdir / (
                    f"{mask_name}_warped_from_{mask_space}_to_"
                    f"{target_std_space}.nii.gz"
                )

                logger.debug(
                    f"Using ANTs to warp {mask_name} "
                    f"from {mask_space} to {target_std_space}"
                )
                # Set antsApplyTransforms command
                apply_transforms_cmd = [
                    "antsApplyTransforms",
                    "-d 3",
                    "-e 3",
                    "-n 'GenericLabel[NearestNeighbor]'",
                    f"-i {mask_path.resolve()}",
                    f"-r {target_std_space_template_path.resolve()}",
                    f"-t {xfm_file_path.resolve()}",
                    f"-o {warped_mask_path.resolve()}",
                ]
                # Call antsApplyTransforms
                run_ext_cmd(
                    name="antsApplyTransforms", cmd=apply_transforms_cmd
                )

                mask_img = nib.load(warped_mask_path)

        all_masks.append(mask_img)

    # Multiple masks, need intersection / union
    if len(all_masks) > 1:
        # Intersect / union of masks
        mask_img = intersect_masks(all_masks, **intersect_params)
    # Single mask
    else:
        if len(intersect_params) > 0:
            # Yes, I'm this strict!
            raise_error(
                "Cannot pass parameters to the intersection function "
                "when there is only one mask."
            )
        mask_img = all_masks[0]

    # Warp mask if target data is native
    if target_space == "native":
        # Save mask image to a component-scoped tempfile
        prewarp_mask_path = tempdir / "prewarp_mask.nii.gz"
        nib.save(mask_img, prewarp_mask_path)

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
    elif t_family == "UKB":
        mask_fname = _load_ukb_mask(name)
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


def _load_ukb_mask(name: str) -> Path:
    """Load UKB mask.

    Parameters
    ----------
    name : {"UKB_15K_GM"}
        The name of the mask.

    Returns
    -------
    pathlib.Path
        File path to the mask image.

    Raises
    ------
    ValueError
        If ``name`` is invalid.

    """
    if name == "UKB_15K_GM":
        mask_fname = "UKB_15K_GM_template.nii.gz"
    else:
        raise_error(f"Cannot find a UKB mask called {name}")

    # Set path for masks
    mask_fname = _masks_path / "ukb" / mask_fname

    return mask_fname
