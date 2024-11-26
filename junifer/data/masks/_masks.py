"""Provide class and function for mask registry and manipulation."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Optional,
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

from ...utils import logger, raise_error
from ...utils.singleton import Singleton
from ..pipeline_data_registry_base import BasePipelineDataRegistry
from ..template_spaces import get_template
from ..utils import closest_resolution, get_native_warper
from ._ants_mask_warper import ANTsMaskWarper
from ._fsl_mask_warper import FSLMaskWarper


if TYPE_CHECKING:
    from nibabel.nifti1 import Nifti1Image


__all__ = ["MaskRegistry", "compute_brain_mask"]


# Path to the masks
_masks_path = Path(__file__).parent


def compute_brain_mask(
    target_data: dict[str, Any],
    extra_input: Optional[dict[str, Any]] = None,
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
        for entry in extra_input["Warp"]:
            if entry["dst"] == "native":
                target_std_space = entry["src"]

    # Fetch template in closest resolution
    template = get_template(
        space=target_std_space,
        target_data=target_data,
        extra_input=extra_input,
        template_type=mask_type,
    )
    # Resample template to target image
    target_img = target_data["data"]
    resampled_template = resample_to_img(
        source_img=template, target_img=target_img
    )

    # Threshold and get mask
    mask = (get_data(resampled_template) >= threshold).astype("int8")

    return new_img_like(target_img, mask)  # type: ignore


class MaskRegistry(BasePipelineDataRegistry, metaclass=Singleton):
    """Class for mask data registry.

    This class is a singleton and is used for managing available mask
    data in a centralized manner.

    """

    def __init__(self) -> None:
        """Initialize the class."""
        # Each entry in registry is a dictionary that must contain at least
        # the following keys:
        # * 'family': the mask's family name
        #             (e.g., 'Vickery-Patil', 'Callable')
        # * 'space': the mask's space (e.g., 'MNI', 'inherit')
        # The built-in masks are files that are shipped with the package in the
        # data/masks directory. The user can also register their own masks.
        # Callable masks should be functions that take at least one parameter:
        # * `target_img`: the image to which the mask will be applied.
        # and should be included in the registry as a value to a key: `func`.
        # The 'family' in that case becomes 'Callable' and 'space' becomes
        # 'inherit'.
        # Make built-in and external dictionaries for validation later
        self._builtin = {}
        self._external = {}

        self._builtin = {
            "GM_prob0.2": {
                "family": "Vickery-Patil",
                "space": "IXI549Space",
            },
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

        # Set built-in to registry
        self._registry = self._builtin

    def register(
        self,
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
            If the mask ``name`` is already registered and
            ``overwrite=False`` or
            if the mask ``name`` is a built-in mask.

        """
        # Check for attempt of overwriting built-in mask
        if name in self._builtin:
            if overwrite:
                logger.info(f"Overwriting mask: {name}")
                if self._registry[name]["family"] != "CustomUserMask":
                    raise_error(
                        f"Mask: {name} already registered as built-in mask."
                    )
            else:
                raise_error(
                    f"Mask: {name} already registered. Set `overwrite=True` "
                    "to update its value."
                )
        # Convert str to Path
        if not isinstance(mask_path, Path):
            mask_path = Path(mask_path)
        logger.info(f"Registering mask: {name}")
        # Add mask info
        self._external[name] = {
            "path": str(mask_path.absolute()),
            "family": "CustomUserMask",
            "space": space,
        }
        # Update registry
        self._registry[name] = {
            "path": str(mask_path.absolute()),
            "family": "CustomUserMask",
            "space": space,
        }

    def deregister(self, name: str) -> None:
        """De-register a custom user mask.

        Parameters
        ----------
        name : str
            The name of the mask.

        """
        logger.info(f"De-registering mask: {name}")
        # Remove mask info
        _ = self._external.pop(name)
        # Update registry
        _ = self._registry.pop(name)

    def load(
        self,
        name: str,
        resolution: Optional[float] = None,
        path_only: bool = False,
    ) -> tuple[Optional[Union["Nifti1Image", Callable]], Optional[Path], str]:
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
        Nifti1Image, callable or None
            Loaded mask image.
        pathlib.Path or None
            File path to the mask image.
        str
            The space of the mask.

        Raises
        ------
        ValueError
            If the ``name`` is invalid or
            if the mask family is invalid.

        """
        # Check for valid mask name
        if name not in self._registry:
            raise_error(
                f"Mask: {name} not found. Valid options are: {self.list}"
            )

        # Copy mask definition to avoid edits in original object
        mask_definition = self._registry[name].copy()
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
            raise_error(f"Unknown mask family: {t_family}")

        # Load mask
        if mask_fname is not None:
            logger.debug(f"Loading mask: {mask_fname.absolute()!s}")
            if not path_only:
                # Load via nibabel
                mask_img = nib.load(mask_fname)

        return mask_img, mask_fname, mask_definition["space"]

    def get(  # noqa: C901
        self,
        masks: Union[str, dict, list[Union[dict, str]]],
        target_data: dict[str, Any],
        extra_input: Optional[dict[str, Any]] = None,
    ) -> "Nifti1Image":
        """Get mask, tailored for the target image.

        Parameters
        ----------
        masks : str, dict or list of dict or str
            The name(s) of the mask(s), or the name(s) of callable mask(s) and
            parameters of the mask(s) as a dictionary. Several masks can be
            passed as a list.
        target_data : dict
            The corresponding item of the data object to which the mask will be
            applied.
        extra_input : dict, optional
            The other fields in the data object. Useful for accessing other
            data kinds that needs to be used in the computation of masks
            (default None).

        Returns
        -------
        Nifti1Image
            The mask image.

        Raises
        ------
        ValueError
            If extra key is provided in addition to mask name in ``masks`` or
            if no mask is provided or
            if ``masks = "inherit"`` and ``mask`` key for the ``target_data``
            is not found or
            if callable parameters are passed to non-callable mask or
            if parameters are passed to :func:`nilearn.masking.intersect_masks`
            when there is only one mask or
            if ``extra_input`` is None when ``target_data``'s space is native.

        """
        # Check pre-requirements for space manipulation
        target_space = target_data["space"]
        # Extra data type requirement check if target space is native
        if target_space == "native":
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
        else:
            # Set target standard space to target space
            target_std_space = target_space

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
                "the name of the mask. The following dictionaries are "
                f"invalid: {invalid_elements}"
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

        # Get all the masks
        all_masks = []
        for t_mask in true_masks:
            if isinstance(t_mask, dict):
                mask_name = next(iter(t_mask.keys()))
                mask_params = t_mask[mask_name]
            else:
                mask_name = t_mask
                mask_params = None

            # If mask is being inherited from the datagrabber or a
            # preprocessor, check that it's accessible
            if mask_name == "inherit":
                if inherited_mask_item is None:
                    raise_error(
                        "Cannot inherit mask from the target data. Either the "
                        "DataGrabber or a Preprocessor does not provide "
                        "`mask` for the target data type."
                    )
                mask_img = inherited_mask_item["data"]
            # Starting with new mask
            else:
                # Load mask
                mask_object, _, mask_space = self.load(
                    mask_name, path_only=False, resolution=resolution
                )
                # Replace mask space with target space if mask's space is
                # inherit
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
                            "Cannot pass callable params to a non-callable "
                            "mask."
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
                    mask_img = ANTsMaskWarper().warp(
                        mask_name=mask_name,
                        mask_img=mask_img,
                        src=mask_space,
                        dst=target_std_space,
                        target_data=target_data,
                        warp_data=None,
                    )

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
            # extra_input check done earlier and warper_spec exists
            if warper_spec["warper"] == "fsl":
                mask_img = FSLMaskWarper().warp(
                    mask_name="native",
                    mask_img=mask_img,
                    target_data=target_data,
                    warp_data=warper_spec,
                )
            elif warper_spec["warper"] == "ants":
                mask_img = ANTsMaskWarper().warp(
                    mask_name="native",
                    mask_img=mask_img,
                    src="",
                    dst="native",
                    target_data=target_data,
                    warp_data=warper_spec,
                )

        return mask_img


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
