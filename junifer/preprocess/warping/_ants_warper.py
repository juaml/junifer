"""Provide class for space warping via ANTs antsApplyTransforms."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import (
    Any,
    ClassVar,
)

import nibabel as nib
import numpy as np

from ...data import get_template, get_xfm
from ...pipeline import WorkDirManager
from ...typing import Dependencies, ExternalDependencies
from ...utils import logger, raise_error, run_ext_cmd


__all__ = ["ANTsWarper"]


class ANTsWarper:
    """Class for space warping via ANTs antsApplyTransforms.

    This class uses ANTs' ``ResampleImage`` for resampling (if required) and
    ``antsApplyTransforms`` for transformation.

    """

    _EXT_DEPENDENCIES: ClassVar[ExternalDependencies] = [
        {
            "name": "ants",
            "commands": ["ResampleImage", "antsApplyTransforms"],
        },
    ]

    _DEPENDENCIES: ClassVar[Dependencies] = {"numpy", "nibabel"}

    def preprocess(
        self,
        input: dict[str, Any],
        extra_input: dict[str, Any],
        reference: str,
    ) -> dict[str, Any]:
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
            The ``input`` dictionary with updated values.

        Raises
        ------
        RuntimeError
            If warp file path could not be found in ``extra_input``.

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
            apply_transforms_out_path = element_tempdir / "warped_data.nii.gz"
            # Set antsApplyTransforms command
            apply_transforms_cmd = [
                "antsApplyTransforms",
                "-d 3",
                "-e 3",
                "-n LanczosWindowedSinc",
                f"-i {input['path'].resolve()}",
                # use resampled reference
                f"-r {resample_image_out_path.resolve()}",
                f"-t {warp_file_path.resolve()}",
                f"-o {apply_transforms_out_path.resolve()}",
            ]
            # Call antsApplyTransforms
            run_ext_cmd(name="antsApplyTransforms", cmd=apply_transforms_cmd)

            logger.debug("Updating warped data")
            input.update(
                {
                    # Update path to sync with "data"
                    "path": apply_transforms_out_path,
                    # Load nifti
                    "data": nib.load(apply_transforms_out_path),
                    # Use reference input's space as warped input's space
                    "space": extra_input["T1w"]["space"],
                    # Save resampled reference path
                    "reference": {"path": resample_image_out_path},
                    # Keep pre-warp space for further operations
                    "prewarp_space": input["space"],
                }
            )

            # Check for data type's mask and warp if found
            if input.get("mask") is not None:
                # Create a tempfile for warped mask output
                apply_transforms_mask_out_path = (
                    element_tempdir / "warped_mask.nii.gz"
                )
                # Set antsApplyTransforms command
                apply_transforms_mask_cmd = [
                    "antsApplyTransforms",
                    "-d 3",
                    "-e 3",
                    "-n 'GenericLabel[NearestNeighbor]'",
                    f"-i {input['mask']['path'].resolve()}",
                    # use resampled reference
                    f"-r {input['reference']['path'].resolve()}",
                    f"-t {warp_file_path.resolve()}",
                    f"-o {apply_transforms_mask_out_path.resolve()}",
                ]
                # Call antsApplyTransforms
                run_ext_cmd(
                    name="antsApplyTransforms", cmd=apply_transforms_mask_cmd
                )

                logger.debug("Updating warped mask data")
                input.update(
                    {
                        "mask": {
                            # Update path to sync with "data"
                            "path": apply_transforms_mask_out_path,
                            # Load nifti
                            "data": nib.load(apply_transforms_mask_out_path),
                            # Use reference input's space as warped input
                            # mask's space
                            "space": extra_input["T1w"]["space"],
                        }
                    }
                )

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
                target_img=input["data"],
                extra_input=None,
            )
            # Save template
            template_space_img_path = (
                element_tempdir / f"{reference}_T1w.nii.gz"
            )
            nib.save(template_space_img, template_space_img_path)

            # Create a tempfile for warped output
            warped_output_path = element_tempdir / (
                f"warped_data_from_{input['space']}_to_{reference}.nii.gz"
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

            logger.debug("Updating warped data")
            input.update(
                {
                    # Update path to sync with "data"
                    "path": warped_output_path,
                    # Load nifti
                    "data": nib.load(warped_output_path),
                    # Update warped input's space
                    "space": reference,
                    # Save reference path
                    "reference": {"path": template_space_img_path},
                    # Keep pre-warp space for further operations
                    "prewarp_space": input["space"],
                }
            )

            # Check for data type's mask and warp if found
            if input.get("mask") is not None:
                # Create a tempfile for warped mask output
                apply_transforms_mask_out_path = element_tempdir / (
                    f"warped_mask_from_{input['space']}_to_"
                    f"{reference}.nii.gz"
                )
                # Set antsApplyTransforms command
                apply_transforms_mask_cmd = [
                    "antsApplyTransforms",
                    "-d 3",
                    "-e 3",
                    "-n 'GenericLabel[NearestNeighbor]'",
                    f"-i {input['mask']['path'].resolve()}",
                    # use resampled reference
                    f"-r {input['reference']['path'].resolve()}",
                    f"-t {xfm_file_path.resolve()}",
                    f"-o {apply_transforms_mask_out_path.resolve()}",
                ]
                # Call antsApplyTransforms
                run_ext_cmd(
                    name="antsApplyTransforms", cmd=apply_transforms_mask_cmd
                )

                logger.debug("Updating warped mask data")
                input.update(
                    {
                        "mask": {
                            # Update path to sync with "data"
                            "path": apply_transforms_mask_out_path,
                            # Load nifti
                            "data": nib.load(apply_transforms_mask_out_path),
                            # Update warped input mask's space
                            "space": reference,
                        }
                    }
                )

        return input
