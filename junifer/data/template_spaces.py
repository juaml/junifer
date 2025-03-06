"""Functions for template space manipulation."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import Any, Optional, Union

import nibabel as nib
import numpy as np
from junifer_data import get
from templateflow import api as tflow

from ..utils import logger, raise_error
from .utils import JUNIFER_DATA_PARAMS, closest_resolution, get_dataset_path


__all__ = ["get_template", "get_xfm"]


def get_xfm(src: str, dst: str) -> Path:  # pragma: no cover
    """Fetch warp files to convert from ``src`` to ``dst``.

    Parameters
    ----------
    src : str
        The template space to transform from.
    dst : str
        The template space to transform to.

    Returns
    -------
    pathlib.Path
        The path to the transformation file.

    """
    # Set file path to retrieve
    xfm_file_path = Path(f"xfms/{src}_to_{dst}/{src}_to_{dst}_Composite.h5")
    # Retrieve file
    return get(
        file_path=xfm_file_path,
        dataset_path=get_dataset_path(),
        **JUNIFER_DATA_PARAMS,
    )


def get_template(
    space: str,
    target_img: nib.Nifti1Image,
    extra_input: Optional[dict[str, Any]] = None,
    template_type: str = "T1w",
    resolution: Optional[Union[int, "str"]] = None,
) -> nib.Nifti1Image:
    """Get template for the space, tailored for the target image.

    Parameters
    ----------
    space : str
        The name of the template space.
    target_img : Nifti1Image
        The corresponding image for which the template space will be loaded.
        This is used to obtain the best matching resolution.
    extra_input : dict, optional
        The other fields in the data object. Useful for accessing other data
        types (default None).
    template_type : {"T1w", "brain", "gm", "wm", "csf"}, optional
        The template type to retrieve (default "T1w").
    resolution : int or "highest", optional
        The resolution of the template to fetch. If None, the closest
        resolution to the target image is used (default None). If "highest",
        the highest resolution is used.

    Returns
    -------
    Nifti1Image
        The template image.

    Raises
    ------
    ValueError
        If ``space`` or ``template_type`` is invalid or
        if ``resolution`` is not at int or "highest".
    RuntimeError
        If required template is not found.

    """
    # Check for invalid space; early check to raise proper error
    if space not in tflow.templates():
        raise_error(f"Unknown template space: {space}")

    # Check for template type
    if template_type not in ["T1w", "brain", "gm", "wm", "csf"]:
        raise_error(f"Unknown template type: {template_type}")

    if isinstance(resolution, str) and resolution != "highest":
        raise_error(
            "Invalid resolution value. Must be an integer or 'highest'"
        )

    # Fetch available resolutions for the template
    available_resolutions = [
        int(min(val["zooms"]))
        for val in tflow.get_metadata(space)["res"].values()
    ]

    # Get the min of the voxels sizes and use it as the resolution
    if resolution is None:
        resolution = np.min(target_img.header.get_zooms()[:3]).astype(int)
    elif resolution == "highest":
        resolution = 0

    # Use the closest resolution if desired resolution is not found
    resolution = closest_resolution(resolution, available_resolutions)

    logger.info(
        f"Downloading template {space} ({template_type} in "
        f"resolution {resolution})"
    )
    # Retrieve template
    try:
        suffix = None
        desc = None
        label = None
        if template_type == "T1w":
            suffix = template_type
            desc = None
            label = None
        elif template_type == "brain":
            suffix = "mask"
            desc = "brain"
            label = None
        elif template_type in ["gm", "wm", "csf"]:
            suffix = "probseg"
            desc = None
            label = template_type.upper()
        # Set kwargs for fetching
        kwargs = {
            "suffix": suffix,
            "desc": desc,
            "label": label,
        }
        template_path = tflow.get(
            space,
            raise_empty=True,
            resolution=resolution,
            extension="nii.gz",
            **kwargs,
        )
    except Exception:  # noqa: BLE001
        raise_error(
            msg=(
                f"Template {space} ({template_type}) with resolution "
                f"{resolution}) not found"
            ),
            klass=RuntimeError,
        )
    else:
        return nib.load(template_path)
