"""Provide class for parcellation space warping via FSL FLIRT."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import uuid
from typing import TYPE_CHECKING, Any

import nibabel as nib

from ...pipeline import WorkDirManager
from ...utils import logger, run_ext_cmd


if TYPE_CHECKING:
    from nibabel.nifti1 import Nifti1Image


__all__ = ["FSLParcellationWarper"]


class FSLParcellationWarper:
    """Class for parcellation space warping via FSL FLIRT.

    This class uses FSL FLIRT's ``applywarp`` for transformation.

    """

    def warp(
        self,
        parcellation_name: str,
        parcellation_img: "Nifti1Image",
        target_data: dict[str, Any],
        warp_data: dict[str, Any],
    ) -> "Nifti1Image":
        """Warp ``parcellation_img`` to correct space.

        Parameters
        ----------
        parcellation_name : str
            The name of the parcellation.
        parcellation_img : nibabel.nifti1.Nifti1Image
            The parcellation image to transform.
        target_data : dict
            The corresponding item of the data object to which the parcellation
            will be applied.
        warp_data : dict
            The warp data item of the data object.

        Returns
        -------
        nibabel.nifti1.Nifti1Image
            The transformed parcellation image.

        """
        logger.debug("Using FSL for parcellation transformation")

        # Create element-scoped tempdir so that warped parcellation is
        # available later as nibabel stores file path reference for
        # loading on computation
        element_tempdir = WorkDirManager().get_element_tempdir(
            prefix=f"fsl_parcellation_warper_{parcellation_name}_{uuid.uuid1()}"
        )

        # Save existing parcellation image to a tempfile
        prewarp_parcellation_path = (
            element_tempdir / "prewarp_parcellation.nii.gz"
        )
        nib.save(parcellation_img, prewarp_parcellation_path)

        # Create a tempfile for warped output
        warped_parcellation_path = (
            element_tempdir / "parcellation_warped.nii.gz"
        )
        # Set applywarp command
        applywarp_cmd = [
            "applywarp",
            "--interp=nn",
            f"-i {prewarp_parcellation_path.resolve()}",
            # use resampled reference
            f"-r {target_data['reference']['path'].resolve()}",
            f"-w {warp_data['path'].resolve()}",
            f"-o {warped_parcellation_path.resolve()}",
        ]
        # Call applywarp
        run_ext_cmd(name="applywarp", cmd=applywarp_cmd)

        # Load nifti
        return nib.load(warped_parcellation_path)
