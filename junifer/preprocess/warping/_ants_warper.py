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

from ...pipeline import WorkDirManager
from ...utils import logger, run_ext_cmd


class ANTsWarper:
    """Class for space warping via ANTs antsApplyTransforms.

    This class uses ANTs' ``ResampleImage`` for resampling and
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
    ) -> Dict[str, Any]:
        """Preprocess using ANTs.

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
        logger.debug("Using ANTs for warping")

        # Get the min of the voxel sizes from input and use it as the
        # resolution
        resolution = np.min(input["data"].header.get_zooms()[:3])

        # Create element-specific tempdir for storing post-warping assets
        element_tempdir = WorkDirManager().get_element_tempdir(
            prefix="ants_warper"
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

        return input
