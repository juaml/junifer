"""Provide class for parcellation space warping via FSL FLIRT."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import uuid
from typing import TYPE_CHECKING, Any, Dict

import nibabel as nib

from ...pipeline import WorkDirManager
from ...utils import logger, raise_error, run_ext_cmd


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
        target_data: Dict[str, Any],
        extra_input: Dict[str, Any],
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
        extra_input : dict, optional
            The other fields in the data object. Useful for accessing other
            data kinds that needs to be used in the computation of
            parcellation.

        Returns
        -------
        nibabel.nifti1.Nifti1Image
            The transformed parcellation image.

        Raises
        ------
        RuntimeError
            If warp file path could not be found in ``extra_input``.

        """
        logger.debug("Using FSL for parcellation transformation")

        # Get warp file path
        warp_file_path = None
        for entry in extra_input["Warp"]:
            if entry["dst"] == "native":
                warp_file_path = entry["path"]
        if warp_file_path is None:
            raise_error(
                klass=RuntimeError, msg="Could not find correct warp file path"
            )

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
            f"-r {target_data['reference_path'].resolve()}",
            f"-w {warp_file_path.resolve()}",
            f"-o {warped_parcellation_path.resolve()}",
        ]
        # Call applywarp
        run_ext_cmd(name="applywarp", cmd=applywarp_cmd)

        # Load nifti
        return nib.load(warped_parcellation_path)