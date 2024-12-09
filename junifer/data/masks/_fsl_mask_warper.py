"""Provide class for mask space warping via FSL FLIRT."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import uuid
from typing import TYPE_CHECKING, Any

import nibabel as nib
import numpy as np

from ...pipeline import WorkDirManager
from ...utils import logger, run_ext_cmd


if TYPE_CHECKING:
    from nibabel.nifti1 import Nifti1Image


__all__ = ["FSLMaskWarper"]


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
        return "nn"
    else:
        return "spline"


class FSLMaskWarper:
    """Class for mask space warping via FSL FLIRT.

    This class uses FSL FLIRT's ``applywarp`` for transformation.

    """

    def warp(
        self,
        mask_name: str,
        mask_img: "Nifti1Image",
        target_data: dict[str, Any],
        warp_data: dict[str, Any],
    ) -> "Nifti1Image":
        """Warp ``mask_img`` to correct space.

        Parameters
        ----------
        mask_name : str
            The name of the mask.
        mask_img : nibabel.nifti1.Nifti1Image
            The mask image to transform.
        target_data : dict
            The corresponding item of the data object to which the mask
            will be applied.
        warp_data : dict
            The warp data item of the data object.

        Returns
        -------
        nibabel.nifti1.Nifti1Image
            The transformed mask image.

        """
        logger.debug("Using FSL for mask transformation")

        # Create element-scoped tempdir so that warped mask is
        # available later as nibabel stores file path reference for
        # loading on computation
        element_tempdir = WorkDirManager().get_element_tempdir(
            prefix=f"fsl_mask_warper_{mask_name}_{uuid.uuid1()}"
        )

        # Save existing mask image to a tempfile
        prewarp_mask_path = element_tempdir / "prewarp_mask.nii.gz"
        nib.save(mask_img, prewarp_mask_path)

        # Create a tempfile for warped output
        warped_mask_path = element_tempdir / "mask_warped.nii.gz"
        # Set applywarp command
        applywarp_cmd = [
            "applywarp",
            f"--interp={_get_interpolation_method(mask_img)}",
            f"-i {prewarp_mask_path.resolve()}",
            # use resampled reference
            f"-r {target_data['reference']['path'].resolve()}",
            f"-w {warp_data['path'].resolve()}",
            f"-o {warped_mask_path.resolve()}",
        ]
        # Call applywarp
        run_ext_cmd(name="applywarp", cmd=applywarp_cmd)

        # Load nifti
        return nib.load(warped_mask_path)
