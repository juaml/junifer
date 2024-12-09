"""Provide class for mask space warping via ANTs."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import uuid
from typing import TYPE_CHECKING, Any, Optional

import nibabel as nib
import numpy as np

from ...pipeline import WorkDirManager
from ...utils import logger, raise_error, run_ext_cmd
from ..template_spaces import get_template, get_xfm


if TYPE_CHECKING:
    from nibabel.nifti1 import Nifti1Image


__all__ = ["ANTsMaskWarper"]


def _get_interpolation_method(img: "Nifti1Image") -> str:
    """Get correct interpolation method for `img`.

    Parameters
    ----------
    img : nibabel.nifti1.Nifti1Image
        The image.

    Returns
    -------
    str
        The interpolation method.

    """
    if np.array_equal(np.unique(img.get_fdata()), [0, 1]):
        return "'GenericLabel[NearestNeighbor]'"
    else:
        return "LanczosWindowedSinc"


class ANTsMaskWarper:
    """Class for mask space warping via ANTs.

    This class uses ANTs ``antsApplyTransforms`` for transformation.

    """

    def warp(
        self,
        mask_name: str,
        mask_img: "Nifti1Image",
        src: str,
        dst: str,
        target_data: dict[str, Any],
        warp_data: Optional[dict[str, Any]],
    ) -> "Nifti1Image":
        """Warp ``mask_img`` to correct space.

        Parameters
        ----------
        mask_name : str
            The name of the mask.
        mask_img : nibabel.nifti1.Nifti1Image
            The mask image to transform.
        src : str
            The data type or template space to warp from.
            It should be empty string if ``dst="native"``.
        dst : str
            The data type or template space to warp to.
            `"native"` is the only allowed data type and it uses the resampled
            T1w found in ``target_data.reference``. The
            ``"reference"`` key is added when :class:`.SpaceWarper` is
            used or if the data is provided native space.
        target_data : dict
            The corresponding item of the data object to which the mask
            will be applied.
        warp_data : dict or None
            The warp data item of the data object. The value is unused if
            ``dst!="native"``.

        Returns
        -------
        nibabel.nifti1.Nifti1Image
            The transformed mask image.

        Raises
        ------
        RuntimeError
            If ``warp_data`` is None when ``dst="T1w"``.

        """
        # Create element-scoped tempdir so that warped mask is
        # available later as nibabel stores file path reference for
        # loading on computation
        prefix = (
            f"ants_mask_warper_{mask_name}"
            f"{'' if not src else f'_from_{src}'}_to_{dst}_"
            f"{uuid.uuid1()}"
        )
        element_tempdir = WorkDirManager().get_element_tempdir(
            prefix=prefix,
        )

        # Native space warping
        if dst == "native":
            # Warp data check
            if warp_data is None:
                raise_error("No `warp_data` provided")
            if "reference" not in target_data:
                raise_error("No `reference` provided")
            if "path" not in target_data["reference"]:
                raise_error("No `path` provided in `reference`")

            logger.debug("Using ANTs for mask transformation")

            # Save existing mask image to a tempfile
            prewarp_mask_path = element_tempdir / "prewarp_mask.nii.gz"
            nib.save(mask_img, prewarp_mask_path)

            # Create a tempfile for warped output
            warped_mask_path = element_tempdir / "mask_warped.nii.gz"
            # Set antsApplyTransforms command
            apply_transforms_cmd = [
                "antsApplyTransforms",
                "-d 3",
                "-e 3",
                "-n 'GenericLabel[NearestNeighbor]'",
                f"-i {prewarp_mask_path.resolve()}",
                # use resampled reference
                f"-r {target_data['reference']['path'].resolve()}",
                f"-t {warp_data['path'].resolve()}",
                f"-o {warped_mask_path.resolve()}",
            ]
            # Call antsApplyTransforms
            run_ext_cmd(name="antsApplyTransforms", cmd=apply_transforms_cmd)

        # Template space warping
        else:
            logger.debug(f"Using ANTs to warp mask from {src} to {dst}")

            # Get xfm file
            xfm_file_path = get_xfm(src=src, dst=dst)
            # Get template space image
            template_space_img = get_template(
                space=dst,
                target_img=mask_img,
                extra_input=None,
            )
            # Save template to a tempfile
            template_space_img_path = element_tempdir / f"{dst}_T1w.nii.gz"
            nib.save(template_space_img, template_space_img_path)

            # Save existing mask image to a tempfile
            prewarp_mask_path = element_tempdir / "prewarp_mask.nii.gz"
            nib.save(mask_img, prewarp_mask_path)

            # Create a tempfile for warped output
            warped_mask_path = element_tempdir / "mask_warped.nii.gz"
            # Set antsApplyTransforms command
            apply_transforms_cmd = [
                "antsApplyTransforms",
                "-d 3",
                "-e 3",
                f"-n {_get_interpolation_method(mask_img)}",
                f"-i {prewarp_mask_path.resolve()}",
                f"-r {template_space_img_path.resolve()}",
                f"-t {xfm_file_path.resolve()}",
                f"-o {warped_mask_path.resolve()}",
            ]
            # Call antsApplyTransforms
            run_ext_cmd(name="antsApplyTransforms", cmd=apply_transforms_cmd)

        # Load nifti
        return nib.load(warped_mask_path)
