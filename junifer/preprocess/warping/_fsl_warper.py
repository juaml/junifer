"""Provide class for space warping via FSL FLIRT."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import (
    Any,
    ClassVar,
)

import nibabel as nib
import numpy as np

from ...pipeline import WorkDirManager
from ...typing import Dependencies, ExternalDependencies
from ...utils import logger, raise_error, run_ext_cmd


__all__ = ["FSLWarper"]


class FSLWarper:
    """Class for space warping via FSL FLIRT.

    This class uses FSL FLIRT's ``flirt`` for resampling and ``applywarp`` for
    transformation.

    """

    _EXT_DEPENDENCIES: ClassVar[ExternalDependencies] = [
        {
            "name": "fsl",
            "commands": ["flirt", "applywarp"],
        },
    ]

    _DEPENDENCIES: ClassVar[Dependencies] = {"numpy", "nibabel"}

    def preprocess(
        self,
        input: dict[str, Any],
        extra_input: dict[str, Any],
        reference: str,
    ) -> dict[str, Any]:  # pragma: no cover
        """Preprocess using FSL.

        Parameters
        ----------
        input : dict
            A single input from the Junifer Data object in which to preprocess.
        extra_input : dict
            The other fields in the Junifer Data object. Should have ``T1w``
            and ``Warp`` data types.
        reference : str
            The data type or template space to use as reference for warping.
            Template space conversion is only possible from native space,
            not from another template space.

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
            prefix="fsl_warper"
        )

        # Warping to native space
        if reference == "T1w":
            logger.debug("Using FSL for space warping")

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
            flirt_out_path = element_tempdir / "resampled_reference.nii.gz"
            # Set flirt command
            flirt_cmd = [
                "flirt",
                "-interp spline",
                f"-in {extra_input['T1w']['path'].resolve()}",
                f"-ref {extra_input['T1w']['path'].resolve()}",
                f"-applyisoxfm {resolution}",
                f"-out {flirt_out_path.resolve()}",
            ]
            # Call flirt
            run_ext_cmd(name="flirt", cmd=flirt_cmd)

            # Create a tempfile for warped output
            applywarp_out_path = element_tempdir / "warped_data.nii.gz"
            # Set applywarp command
            applywarp_cmd = [
                "applywarp",
                "--interp=spline",
                f"-i {input['path'].resolve()}",
                # use resampled reference
                f"-r {flirt_out_path.resolve()}",
                f"-w {warp_file_path.resolve()}",
                f"-o {applywarp_out_path.resolve()}",
            ]
            # Call applywarp
            run_ext_cmd(name="applywarp", cmd=applywarp_cmd)

            logger.debug("Updating warped data")
            input.update(
                {
                    # Update path to sync with "data"
                    "path": applywarp_out_path,
                    # Load nifti
                    "data": nib.load(applywarp_out_path),
                    # Use reference input's space as warped input's space
                    "space": extra_input["T1w"]["space"],
                    # Save resampled reference path
                    "reference": {"path": flirt_out_path},
                    # Keep pre-warp space for further operations
                    "prewarp_space": input["space"],
                }
            )

            # Check for data type's mask and warp if found
            if input.get("mask") is not None:
                # Create a tempfile for warped mask output
                applywarp_mask_out_path = (
                    element_tempdir / "warped_mask.nii.gz"
                )
                # Set applywarp command
                applywarp_mask_cmd = [
                    "applywarp",
                    "--interp=nn",
                    f"-i {input['mask']['path'].resolve()}",
                    # use resampled reference
                    f"-r {input['reference']['path'].resolve()}",
                    f"-w {warp_file_path.resolve()}",
                    f"-o {applywarp_mask_out_path.resolve()}",
                ]
                # Call applywarp
                run_ext_cmd(name="applywarp", cmd=applywarp_mask_cmd)

                logger.debug("Updating warped mask data")
                input.update(
                    {
                        "mask": {
                            # Update path to sync with "data"
                            "path": applywarp_mask_out_path,
                            # Load nifti
                            "data": nib.load(applywarp_mask_out_path),
                            # Use reference input's space as warped input
                            # mask's space
                            "space": extra_input["T1w"]["space"],
                        }
                    }
                )

        # Warping from native to template space
        else:
            logger.debug(
                f"Using FSL to warp data from native space to {reference} "
                "space"
            )

            # Get warp file path
            warp_file_path = None
            for entry in extra_input["Warp"]:
                if entry["src"] == "native" and entry["dst"] == reference:
                    warp_file_path = entry["path"]
            if warp_file_path is None:
                raise_error(
                    klass=RuntimeError,
                    msg="Could not find correct warp file path",
                )

            # Use flirt if input data resolution and reference resolution don't
            # match
            input_resolution = np.min(input["data"].header.get_zooms()[:3])
            ref_resolution = np.min(
                input["reference"]["data"].header.get_zooms()[:3]
            )
            logger.debug(f"Input resolution: {input_resolution}")
            logger.debug(f"Reference resolution: {ref_resolution}")
            if input_resolution != ref_resolution:
                logger.debug("Resampling reference to match input resolution")
                # Create a tempfile for resampled reference output
                ref_path = (
                    element_tempdir / f"resampled_reference-{reference}.nii.gz"
                )
                # Set flirt command
                flirt_cmd = [
                    "flirt",
                    "-interp spline",
                    f"-in {input['reference']['path'].resolve()}",
                    f"-ref {input['reference']['path'].resolve()}",
                    f"-applyisoxfm {input_resolution}",
                    f"-out {ref_path.resolve()}",
                ]
                # Call flirt
                run_ext_cmd(name="flirt", cmd=flirt_cmd)
            else:
                logger.debug("Reference resolution matches input resolution")
                ref_path = input["reference"]["path"]

            # Create a tempfile for warped output
            applywarp_out_path = (
                element_tempdir
                / f"warped_data_from_native_to_{reference}.nii.gz"
            )
            # Set applywarp command
            applywarp_cmd = [
                "applywarp",
                "--interp=spline",
                f"-i {input['path'].resolve()}",
                # use resampled reference or original
                f"-r {ref_path.resolve()}",
                f"-w {warp_file_path.resolve()}",
                f"-o {applywarp_out_path.resolve()}",
            ]
            # Call applywarp
            run_ext_cmd(name="applywarp", cmd=applywarp_cmd)

            logger.debug("Updating warped data")
            input.update(
                {
                    # Update path to sync with "data"
                    "path": applywarp_out_path,
                    # Load nifti
                    "data": nib.load(applywarp_out_path),
                    # Switch space and prewarp_space
                    "space": reference,
                    "prewarp_space": input["space"],
                    # Save resampled reference path or overwrite original
                    # keeping it same
                    "reference": {"path": ref_path},
                }
            )

            # Check for data type's mask and warp if found
            if input.get("mask") is not None:
                logger.debug("Warping associated mask")
                # Create a tempfile for warped mask output
                applywarp_mask_out_path = (
                    element_tempdir
                    / f"warped_mask_from_native_to_{reference}.nii.gz"
                )
                # Set applywarp command
                applywarp_mask_cmd = [
                    "applywarp",
                    "--interp=nn",
                    f"-i {input['mask']['path'].resolve()}",
                    # use resampled reference or original
                    f"-r {ref_path.resolve()}",
                    f"-w {warp_file_path.resolve()}",
                    f"-o {applywarp_mask_out_path.resolve()}",
                ]
                # Call applywarp
                run_ext_cmd(name="applywarp", cmd=applywarp_mask_cmd)

                logger.debug("Updating warped mask data")
                input.update(
                    {
                        "mask": {
                            # Update path to sync with "data"
                            "path": applywarp_mask_out_path,
                            # Load nifti
                            "data": nib.load(applywarp_mask_out_path),
                            # Update mask's space
                            "space": reference,
                        }
                    }
                )

        return input
