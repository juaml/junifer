"""Provide class for parcellation space warping via ANTs."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import uuid
from typing import TYPE_CHECKING, Any, Dict, Optional

import nibabel as nib

from ...pipeline import WorkDirManager
from ...utils import logger, raise_error, run_ext_cmd
from ..template_spaces import get_template, get_xfm


if TYPE_CHECKING:
    from nibabel.nifti1 import Nifti1Image


__all__ = ["ANTsParcellationWarper"]


class ANTsParcellationWarper:
    """Class for parcellation space warping via ANTs.

    This class uses ANTs ``antsApplyTransforms`` for transformation.

    """

    def warp(
        self,
        parcellation_name: str,
        parcellation_img: "Nifti1Image",
        src: str,
        dst: str,
        target_data: Dict[str, Any],
        extra_input: Optional[Dict[str, Any]] = None,
    ) -> "Nifti1Image":
        """Warp ``parcellation_img`` to correct space.

        Parameters
        ----------
        parcellation_name : str
            The name of the parcellation.
        parcellation_img : nibabel.nifti1.Nifti1Image
            The parcellation image to transform.
        src : str
            The data type or template space to warp from.
            It should be empty string if ``dst="T1w"``.
        dst : str
            The data type or template space to warp to.
            `"T1w"` is the only allowed data type and it uses the resampled T1w
            found in ``target_data.reference_path``. The ``"reference_path"``
            key is added when :class:`.SpaceWarper` is used.
        target_data : dict
            The corresponding item of the data object to which the parcellation
            will be applied.
        extra_input : dict, optional
            The other fields in the data object. Useful for accessing other
            data kinds that needs to be used in the computation of parcellation
            (default None).


        Returns
        -------
        nibabel.nifti1.Nifti1Image
            The transformed parcellation image.

        Raises
        ------
        RuntimeError
            If warp file path could not be found in ``extra_input``.

        """
        # Create element-scoped tempdir so that warped parcellation is
        # available later as nibabel stores file path reference for
        # loading on computation
        prefix = (
            f"ants_parcellation_warper_{parcellation_name}"
            f"{'' if not src else f'_from_{src}'}_to_{dst}_"
            f"{uuid.uuid1()}"
        )
        element_tempdir = WorkDirManager().get_element_tempdir(
            prefix=prefix,
        )

        # Native space warping
        if dst == "T1w":
            logger.debug("Using ANTs for parcellation transformation")

            # Get warp file path
            warp_file_path = None
            for entry in extra_input["Warp"]:
                if entry["dst"] == "native":
                    warp_file_path = entry["path"]
            if warp_file_path is None:
                raise_error(
                    klass=RuntimeError,
                    msg="Could not find correct warp file path",
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
            # Set antsApplyTransforms command
            apply_transforms_cmd = [
                "antsApplyTransforms",
                "-d 3",
                "-e 3",
                "-n 'GenericLabel[NearestNeighbor]'",
                f"-i {prewarp_parcellation_path.resolve()}",
                # use resampled reference
                f"-r {target_data['reference_path'].resolve()}",
                f"-t {warp_file_path.resolve()}",
                f"-o {warped_parcellation_path.resolve()}",
            ]
            # Call antsApplyTransforms
            run_ext_cmd(name="antsApplyTransforms", cmd=apply_transforms_cmd)

        # Template space warping
        else:
            logger.debug(
                f"Using ANTs to warp parcellation from {src} to {dst}"
            )

            # Get xfm file
            xfm_file_path = get_xfm(src=src, dst=dst)
            # Get template space image
            template_space_img = get_template(
                space=dst,
                target_data=target_data,
                extra_input=None,
            )
            # Save template to a tempfile
            template_space_img_path = element_tempdir / f"{dst}_T1w.nii.gz"
            nib.save(template_space_img, template_space_img_path)

            # Save existing parcellation image to a tempfile
            prewarp_parcellation_path = (
                element_tempdir / "prewarp_parcellation.nii.gz"
            )
            nib.save(parcellation_img, prewarp_parcellation_path)

            # Create a tempfile for warped output
            warped_parcellation_path = (
                element_tempdir / "parcellation_warped.nii.gz"
            )
            # Set antsApplyTransforms command
            apply_transforms_cmd = [
                "antsApplyTransforms",
                "-d 3",
                "-e 3",
                "-n 'GenericLabel[NearestNeighbor]'",
                f"-i {prewarp_parcellation_path.resolve()}",
                f"-r {template_space_img_path.resolve()}",
                f"-t {xfm_file_path.resolve()}",
                f"-o {warped_parcellation_path.resolve()}",
            ]
            # Call antsApplyTransforms
            run_ext_cmd(name="antsApplyTransforms", cmd=apply_transforms_cmd)

        # Load nifti
        return nib.load(warped_parcellation_path)