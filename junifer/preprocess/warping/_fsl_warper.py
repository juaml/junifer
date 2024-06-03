"""Provide class for space warping via FSL FLIRT."""

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

from ...pipeline import WorkDirManager
from ...utils import logger, run_ext_cmd


__all__ = ["FSLWarper"]


class FSLWarper:
    """Class for space warping via FSL FLIRT.

    This class uses FSL FLIRT's ``flirt`` for resampling and ``applywarp`` for
    transformation.

    """

    _EXT_DEPENDENCIES: ClassVar[List[Dict[str, Union[str, List[str]]]]] = [
        {
            "name": "fsl",
            "commands": ["flirt", "applywarp"],
        },
    ]

    _DEPENDENCIES: ClassVar[Set[str]] = {"numpy", "nibabel"}

    def preprocess(
        self,
        input: Dict[str, Any],
        extra_input: Dict[str, Any],
    ) -> Dict[str, Any]:
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
            values and new ``reference_path`` key whose value points to the
            reference file used for warping.

        """
        logger.debug("Using FSL for space warping")

        # Get the min of the voxel sizes from input and use it as the
        # resolution
        resolution = np.min(input["data"].header.get_zooms()[:3])

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
            f"-w {extra_input['Warp']['path'].resolve()}",
            f"-o {applywarp_out_path.resolve()}",
        ]
        # Call applywarp
        run_ext_cmd(name="applywarp", cmd=applywarp_cmd)

        # Load nifti
        input["data"] = nib.load(applywarp_out_path)
        # Save resampled reference path
        input["reference_path"] = flirt_out_path

        # Use reference input's space as warped input's space
        input["space"] = extra_input["T1w"]["space"]

        return input
