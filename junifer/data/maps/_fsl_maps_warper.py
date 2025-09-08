"""Provide class for maps space warping via FSL FLIRT."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import uuid
from typing import TYPE_CHECKING, Any

import nibabel as nib

from ...pipeline import WorkDirManager
from ...utils import logger, run_ext_cmd


if TYPE_CHECKING:
    from nibabel.nifti1 import Nifti1Image


__all__ = ["FSLMapsWarper"]


class FSLMapsWarper:
    """Class for maps space warping via FSL FLIRT.

    This class uses FSL FLIRT's ``applywarp`` for transformation.

    """

    def warp(
        self,
        maps_name: str,
        maps_img: "Nifti1Image",
        target_data: dict[str, Any],
        warp_data: dict[str, Any],
    ) -> "Nifti1Image":  # pragma: no cover
        """Warp ``maps_img`` to correct space.

        Parameters
        ----------
        maps_name : str
            The name of the maps.
        maps_img : nibabel.nifti1.Nifti1Image
            The maps image to transform.
        target_data : dict
            The corresponding item of the data object to which the maps
            will be applied.
        warp_data : dict
            The warp data item of the data object.

        Returns
        -------
        nibabel.nifti1.Nifti1Image
            The transformed maps image.

        """
        logger.debug("Using FSL for maps transformation")

        # Create element-scoped tempdir so that warped maps is
        # available later as nibabel stores file path reference for
        # loading on computation
        element_tempdir = WorkDirManager().get_element_tempdir(
            prefix=f"fsl_maps_warper_{maps_name}_{uuid.uuid1()}"
        )

        # Save existing maps image to a tempfile
        prewarp_maps_path = element_tempdir / "prewarp_maps.nii.gz"
        nib.save(maps_img, prewarp_maps_path)

        # Create a tempfile for warped output
        warped_maps_path = element_tempdir / "maps_warped.nii.gz"
        # Set applywarp command
        applywarp_cmd = [
            "applywarp",
            "--interp=spline",
            f"-i {prewarp_maps_path.resolve()}",
            # use resampled reference
            f"-r {target_data['reference']['path'].resolve()}",
            f"-w {warp_data['path'].resolve()}",
            f"-o {warped_maps_path.resolve()}",
        ]
        # Call applywarp
        run_ext_cmd(name="applywarp", cmd=applywarp_cmd)

        # Load nifti
        return nib.load(warped_maps_path)
