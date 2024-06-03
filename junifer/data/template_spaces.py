"""Functions for template space manipulation."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import Any, Dict, Optional, Union

import httpx
import nibabel as nib
import numpy as np
from templateflow import api as tflow

from ..utils import logger, raise_error
from .utils import closest_resolution


__all__ = ["get_xfm", "get_template"]


def get_xfm(
    src: str, dst: str, xfms_dir: Union[str, Path, None] = None
) -> Path:  # pragma: no cover
    """Fetch warp files to convert from ``src`` to ``dst``.

    Parameters
    ----------
    src : str
        The template space to transform from.
    dst : str
        The template space to transform to.
    xfms_dir : str or pathlib.Path, optional
        Path where the retrieved transformation files are stored.
        The default location is "$HOME/junifer/data/xfms" (default None).

    Returns
    -------
    pathlib.Path
        The path to the transformation file.

    Raises
    ------
    RuntimeError
        If there is a problem fetching files.

    """
    if xfms_dir is None:
        xfms_dir = Path().home() / "junifer" / "data" / "xfms"
        logger.debug(f"Creating xfm directory at: {xfms_dir.resolve()}")
        # Create default junifer data directory if not present
        xfms_dir.mkdir(exist_ok=True, parents=True)
    # Convert str to Path
    elif not isinstance(xfms_dir, Path):
        xfms_dir = Path(xfms_dir)

    # Set local file prefix
    xfm_file_prefix = f"{src}_to_{dst}"
    # Set local file dir
    xfm_file_dir = xfms_dir / xfm_file_prefix
    # Create local directory if not present
    xfm_file_dir.mkdir(exist_ok=True, parents=True)
    # Set file name with extension
    xfm_file = f"{src}_to_{dst}_Composite.h5"
    # Set local file path
    xfm_file_path = xfm_file_dir / xfm_file
    # Check if the file exists
    if xfm_file_path.exists():
        logger.info(
            f"Found existing xfm file for {src} to {dst} at "
            f"{xfm_file_path.resolve()}"
        )
        return xfm_file_path

    # Set URL
    url = (
        "https://gin.g-node.org/juaml/human-template-xfms/raw/main/xfms/"
        f"{xfm_file_prefix}/{xfm_file}"
    )
    # Create the file before proceeding
    xfm_file_path.touch()

    logger.info(f"Downloading xfm file for {src} to {dst} from {url}")
    # Steam response
    with httpx.stream("GET", url) as resp:
        try:
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise_error(
                f"Error response {exc.response.status_code} while "
                f"requesting {exc.request.url!r}",
                klass=RuntimeError,
            )
        else:
            with open(xfm_file_path, "ab") as f:
                for chunk in resp.iter_bytes():
                    f.write(chunk)

    return xfm_file_path


def get_template(
    space: str,
    target_data: Dict[str, Any],
    extra_input: Optional[Dict[str, Any]] = None,
    template_type: str = "T1w",
) -> nib.Nifti1Image:
    """Get template for the space, tailored for the target image.

    Parameters
    ----------
    space : str
        The name of the template space.
    target_data : dict
        The corresponding item of the data object for which the template space
        will be loaded.
    extra_input : dict, optional
        The other fields in the data object. Useful for accessing other data
        types (default None).
    template_type : {"T1w", "brain", "gm", "wm", "csf"}, optional
        The template type to retrieve (default "T1w").

    Returns
    -------
    Nifti1Image
        The template image.

    Raises
    ------
    ValueError
        If ``space`` or ``template_type`` is invalid.
    RuntimeError
        If required template is not found.

    """
    # Check for invalid space; early check to raise proper error
    if space not in tflow.templates():
        raise_error(f"Unknown template space: {space}")

    # Check for template type
    if template_type not in ["T1w", "brain", "gm", "wm", "csf"]:
        raise_error(f"Unknown template type: {template_type}")

    # Get the min of the voxels sizes and use it as the resolution
    target_img = target_data["data"]
    resolution = np.min(target_img.header.get_zooms()[:3]).astype(int)

    # Fetch available resolutions for the template
    available_resolutions = [
        int(min(val["zooms"]))
        for val in tflow.get_metadata(space)["res"].values()
    ]
    # Use the closest resolution if desired resolution is not found
    resolution = closest_resolution(resolution, available_resolutions)

    logger.info(f"Downloading template {space} in resolution {resolution}")
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
            f"Template {space} ({template_type}) with resolution {resolution} "
            "not found",
            klass=RuntimeError,
        )
    else:
        return nib.load(template_path)  # type: ignore
