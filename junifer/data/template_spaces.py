"""Functions for template space manipulation."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import re
from functools import cache
from pathlib import Path
from typing import Any, Union

import nibabel as nib
import numpy as np
import structlog
from junifer_data import get
from templateflow import api as tflow

from ..typing import SpaceLike
from ..utils import raise_error
from .utils import JUNIFER_DATA_PARAMS, closest_resolution, get_dataset_path


__all__ = ["get_template", "get_xfm"]

_log = structlog.get_logger("junifer")
logger = _log.bind(pkg="data")


@cache
def _get_templateflow_templates() -> frozenset[str]:
    """Get the available templateflow template spaces.

    Querying templateflow scans its whole layout, so the result is cached.

    Returns
    -------
    frozenset of str
        The available template spaces.

    """
    return frozenset(tflow.templates())


def get_xfm(src: SpaceLike, dst: SpaceLike) -> Path:  # pragma: no cover
    """Fetch warp files to convert from ``src`` to ``dst``.

    Parameters
    ----------
    src : str or Enum
        The template space to transform from.
    dst : str or Enum
        The template space to transform to.

    Returns
    -------
    pathlib.Path
        The path to the transformation file.

    """
    # Normalise enum-based spaces (e.g. `AOMICSpace`) to their values
    src = getattr(src, "value", src)
    dst = getattr(dst, "value", dst)
    # Set file path to retrieve
    xfm_file_path = Path(f"xfms/{src}_to_{dst}/{src}_to_{dst}_Composite.h5")
    # Retrieve file
    return get(
        file_path=xfm_file_path,
        dataset_path=get_dataset_path(),
        **JUNIFER_DATA_PARAMS,
    )


def _get_template_resolutions(
    space: str, entities: dict[str, str | None]
) -> dict[int, float]:
    """Get the resolutions of a template that have the given files.

    Not every resolution of a template has every file (e.g., in
    templateflow 25, MNI152NLin2009cAsym lists resolutions 3 and 4, but has
    no brain mask for them), and the resolution index is not the voxel size
    (e.g., resolution 3 of MNI152NLin6Asym is 0.5mm).

    Parameters
    ----------
    space : str
        The name of the template space.
    entities : dict
        The templateflow entities of the files (e.g., ``suffix``).

    Returns
    -------
    dict
        The voxel size (in mm) of each resolution index with files.

    """
    # The voxel size of each resolution index. Indices are compared as
    # integers, as file names can use "1" while metadata uses "01"
    voxel_sizes = {
        int(index): float(min(info["zooms"]))
        for index, info in tflow.get_metadata(space)["res"].items()
    }
    # List the files without downloading them and keep their resolutions
    resolutions = {}
    for path in tflow.ls(space, extension="nii.gz", **entities):
        match = re.search(r"_res-(\d+)_", Path(path).name)
        if match is not None and int(match.group(1)) in voxel_sizes:
            index = int(match.group(1))
            resolutions[index] = voxel_sizes[index]
    return resolutions


def get_template(
    space: SpaceLike,
    target_img: nib.Nifti1Image,
    extra_input: dict[str, Any] | None = None,
    template_type: str = "T1w",
    resolution: Union[int, "str"] | None = None,
) -> nib.Nifti1Image:
    """Get template for the space, tailored for the target image.

    Parameters
    ----------
    space : str or Enum
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
        The resolution (voxel size in mm) of the template to fetch. If None,
        the closest resolution to the target image is used (default None).
        If "highest", the highest resolution is used.

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
    # Normalise enum-based spaces (e.g. `AOMICSpace`) to their values
    space = getattr(space, "value", space)
    # Check for invalid space; early check to raise proper error
    if space not in _get_templateflow_templates():
        raise_error(f"Unknown template space: {space}")

    # Check for template type
    if template_type not in ["T1w", "brain", "gm", "wm", "csf"]:
        raise_error(f"Unknown template type: {template_type}")

    if isinstance(resolution, str) and resolution != "highest":
        raise_error(
            "Invalid resolution value. Must be an integer or 'highest'"
        )

    # Get the templateflow entities of the template type
    if template_type == "T1w":
        entities = {"suffix": "T1w", "desc": None, "label": None}
    elif template_type == "brain":
        entities = {"suffix": "mask", "desc": "brain", "label": None}
    else:
        entities = {
            "suffix": "probseg",
            "desc": None,
            "label": template_type.upper(),
        }

    # Get the resolutions that have the template type
    resolutions = _get_template_resolutions(space, entities)
    if not resolutions:
        raise_error(
            msg=f"Template {space} ({template_type}) not found",
            klass=RuntimeError,
        )

    # Get the desired voxel size; None means the highest resolution
    if resolution == "highest":
        desired_voxel_size = None
    elif resolution is None:
        desired_voxel_size = float(np.min(target_img.header.get_zooms()[:3]))
    else:
        desired_voxel_size = resolution

    # Use the closest voxel size if the desired one is not available
    voxel_size = closest_resolution(
        desired_voxel_size, list(resolutions.values())
    )
    # Get the resolution index of that voxel size
    res_index = {size: index for index, size in resolutions.items()}[
        voxel_size
    ]

    logger.info(
        f"Downloading template {space} ({template_type} in "
        f"resolution {voxel_size}mm)"
    )
    # Retrieve template
    try:
        template_path = tflow.get(
            space,
            raise_empty=True,
            resolution=res_index,
            extension="nii.gz",
            **entities,
        )
    except Exception:  # noqa: BLE001
        raise_error(
            msg=(
                f"Template {space} ({template_type}) with resolution "
                f"{voxel_size}mm not found"
            ),
            klass=RuntimeError,
        )
    else:
        return nib.load(template_path)
