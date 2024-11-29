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
    ) -> dict[str, Any]:
        """Preprocess using FSL.

        Parameters
        ----------
        input : dict
            A single input from the Junifer Data object in which to preprocess.
        extra_input : dict
            The other fields in the Junifer Data object. Should have ``T1w``
            and ``Warp`` data types.

        Returns
        -------
        dict
            The ``input`` dictionary with modified ``data`` and ``space`` key
            values and new ``reference`` key whose value points to the
            reference file used for warping.

        Raises
        ------
        RuntimeError
            If warp file path could not be found in ``extra_input``.

        """
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
                klass=RuntimeError, msg="Could not find correct warp file path"
            )

        # Create element-specific tempdir for storing post-warping assets
        element_tempdir = WorkDirManager().get_element_tempdir(
            prefix="fsl_warper"
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
        applywarp_out_path = element_tempdir / "output.nii.gz"
        # Set applywarp command
        applywarp_cmd = [
            "applywarp",
            "--interp=spline",
            f"-i {input['path'].resolve()}",
            f"-r {flirt_out_path.resolve()}",  # use resampled reference
            f"-w {warp_file_path.resolve()}",
            f"-o {applywarp_out_path.resolve()}",
        ]
        # Call applywarp
        run_ext_cmd(name="applywarp", cmd=applywarp_cmd)

        # Load nifti
        input["data"] = nib.load(applywarp_out_path)
        # Save resampled reference path
        input["reference"] = {"path": flirt_out_path}
        # Keep pre-warp space for further operations
        input["prewarp_space"] = input["space"]
        # Use reference input's space as warped input's space
        input["space"] = extra_input["T1w"]["space"]

        return input
