"""Provide class for space warping via ANTs antsApplyTransforms."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import (
    Any,
    ClassVar,
    Dict,
    List,
    Set,
    Union,
)

import nibabel as nib
import numpy as np

from ...data import get_template, get_xfm
from ...pipeline import WorkDirManager
from ...utils import logger, run_ext_cmd


__all__ = ["ANTsWarper"]


class ANTsWarper:
    """Class for space warping via ANTs antsApplyTransforms.

    This class uses ANTs' ``ResampleImage`` for resampling (if required) and
    ``antsApplyTransforms`` for transformation.

    """

    _EXT_DEPENDENCIES: ClassVar[List[Dict[str, Union[str, List[str]]]]] = [
        {
            "name": "ants",
            "commands": ["ResampleImage", "antsApplyTransforms"],
        },
    ]

    _DEPENDENCIES: ClassVar[Set[str]] = {"numpy", "nibabel"}

    def preprocess(
        self,
        input: Dict[str, Any],
        extra_input: Dict[str, Any],
        reference: str,
    ) -> Dict[str, Any]:
        """Preprocess using ANTs.

        Parameters
        ----------
        input : dict
            A single input from the Junifer Data object in which to preprocess.
        extra_input : dict
            The other fields in the Junifer Data object. Should have ``T1w``
            and ``Warp`` data types.
        reference : str
            The data type or template space to use as reference for warping.

        Returns
        -------
        dict
            The ``input`` dictionary with modified ``data`` and ``space`` key
            values and new ``reference_path`` key whose value points to the
            reference file used for warping.

        """
        # Create element-specific tempdir for storing post-warping assets
        element_tempdir = WorkDirManager().get_element_tempdir(
            prefix="ants_warper"
        )

        # Native space warping
        if reference == "T1w":
            logger.debug("Using ANTs for space warping")

            # Get the min of the voxel sizes from input and use it as the
            # resolution
            resolution = np.min(input["data"].header.get_zooms()[:3])

            # Create a tempfile for resampled reference output
            resample_image_out_path = (
                element_tempdir / "resampled_reference.nii.gz"
            )
            # Set ResampleImage command
            resample_image_cmd = [
                "ResampleImage",
                "3",  # image dimension
                f"{extra_input['T1w']['path'].resolve()}",
                f"{resample_image_out_path.resolve()}",
                f"{resolution}x{resolution}x{resolution}",
                "0",  # option for spacing and not size
                "3 3",  # Lanczos windowed sinc
            ]
            # Call ResampleImage
            run_ext_cmd(name="ResampleImage", cmd=resample_image_cmd)

            # Create a tempfile for warped output
            apply_transforms_out_path = element_tempdir / "output.nii.gz"
            # Set antsApplyTransforms command
            apply_transforms_cmd = [
                "antsApplyTransforms",
                "-d 3",
                "-e 3",
                "-n LanczosWindowedSinc",
                f"-i {input['path'].resolve()}",
                # use resampled reference
                f"-r {resample_image_out_path.resolve()}",
                f"-t {extra_input['Warp']['path'].resolve()}",
                f"-o {apply_transforms_out_path.resolve()}",
            ]
            # Call antsApplyTransforms
            run_ext_cmd(name="antsApplyTransforms", cmd=apply_transforms_cmd)

            # Load nifti
            input["data"] = nib.load(apply_transforms_out_path)
            # Save resampled reference path
            input["reference_path"] = resample_image_out_path
            # Use reference input's space as warped input's space
            input["space"] = extra_input["T1w"]["space"]

        # Template space warping
        else:
            logger.debug(
                f"Using ANTs to warp data from {input['space']} to {reference}"
            )

            # Get xfm file
            xfm_file_path = get_xfm(src=input["space"], dst=reference)
            # Get template space image
            template_space_img = get_template(
                space=reference,
                target_data=input,
                extra_input=None,
            )

            # Create component-scoped tempdir
            tempdir = WorkDirManager().get_tempdir(prefix="ants_warper")
            # Save template
            template_space_img_path = tempdir / f"{reference}_T1w.nii.gz"
            nib.save(template_space_img, template_space_img_path)

            # Create a tempfile for warped output
            warped_output_path = element_tempdir / (
                f"data_warped_from_{input['space']}_to_" f"{reference}.nii.gz"
            )

            # Set antsApplyTransforms command
            apply_transforms_cmd = [
                "antsApplyTransforms",
                "-d 3",
                "-e 3",
                "-n LanczosWindowedSinc",
                f"-i {input['path'].resolve()}",
                f"-r {template_space_img_path.resolve()}",
                f"-t {xfm_file_path.resolve()}",
                f"-o {warped_output_path.resolve()}",
            ]
            # Call antsApplyTransforms
            run_ext_cmd(name="antsApplyTransforms", cmd=apply_transforms_cmd)

            # Delete tempdir
            WorkDirManager().delete_tempdir(tempdir)

            # Modify target data
            input["data"] = nib.load(warped_output_path)
            input["space"] = reference

        return input
