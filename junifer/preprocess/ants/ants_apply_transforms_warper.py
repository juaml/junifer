"""Provide class for warping via ANTs antsApplyTransforms."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import subprocess
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
    cast,
)

import nibabel as nib
import numpy as np

from ...pipeline import WorkDirManager
from ...utils import logger, raise_error
from ..base import BasePreprocessor


if TYPE_CHECKING:
    from nibabel import Nifti1Image


class _AntsApplyTransformsWarper(BasePreprocessor):
    """Class for warping NIfTI images via ANTs antsApplyTransforms.

    Warps ANTs ``antsApplyTransforms``.

    Parameters
    ----------
    reference : str
        The data type to use as reference for warping.
    on : str
        The data type to use for warping.

    Raises
    ------
    ValueError
        If a list was passed for ``on``.

    """

    _EXT_DEPENDENCIES: ClassVar[
        List[Dict[str, Union[str, bool, List[str]]]]
    ] = [
        {
            "name": "ants",
            "optional": False,
            "commands": ["ResampleImage", "antsApplyTransforms"],
        },
    ]

    def __init__(self, reference: str, on: str) -> None:
        """Initialize the class."""
        self.ref = reference
        # Check only single data type is passed
        if isinstance(on, list):
            raise_error("Can only work on single data type, list was passed.")
        self.on = on  # needed for the base validation to work
        super().__init__(
            on=self.on, required_data_types=[self.on, self.ref, "Warp"]
        )

    def get_valid_inputs(self) -> List[str]:
        """Get valid data types for input.

        Returns
        -------
        list of str
            The list of data types that can be used as input for this
            preprocessor.

        """
        # Constructed dynamically
        return [self.on]

    def get_output_type(self, input: List[str]) -> List[str]:
        """Get output type.

        Parameters
        ----------
        input : list of str
            The input to the preprocessor. The list must contain the
            available Junifer Data dictionary keys.

        Returns
        -------
        list of str
            The updated list of available Junifer Data object keys after
            the pipeline step.

        """
        # Does not add any new keys
        return input

    def _run_apply_transforms(
        self,
        input_data: Dict,
        ref_path: Path,
        warp_path: Path,
    ) -> Tuple["Nifti1Image", Path]:
        """Run ``antsApplyTransforms``.

        Parameters
        ----------
        input_data : dict
            The input data.
        ref_path : pathlib.Path
            The path to the reference file.
        warp_path : pathlib.Path
            The path to the warp file.

        Returns
        -------
        Niimg-like object
            The warped input image.
        pathlib.Path
            The path to the resampled reference image.

        Raises
        ------
        RuntimeError
            If ANTs command fails.

        """
        # Get the min of the voxel sizes from input and use it as the
        # resolution
        resolution = np.min(input_data["data"].header.get_zooms()[:3])

        # Create element-specific tempdir for storing post-warping assets
        tempdir = WorkDirManager().get_element_tempdir(
            prefix="applytransforms"
        )

        # Create a tempfile for resampled reference output
        resample_image_out_path = tempdir / "reference_resampled.nii.gz"
        # Set ResampleImage command
        resample_image_cmd = [
            "ResampleImage",
            "3",  # image dimension
            f"{ref_path.resolve()}",
            f"{resample_image_out_path.resolve()}",
            f"{resolution}x{resolution}x{resolution}",
            "0",  # option for spacing and not size
            "3 3",  # Lanczos windowed sinc
        ]
        # Call ResampleImage
        resample_image_cmd_str = " ".join(resample_image_cmd)
        logger.info(
            f"ResampleImage command to be executed: {resample_image_cmd_str}"
        )
        resample_image_process = subprocess.run(
            resample_image_cmd_str,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,  # needed for respecting $PATH
            check=False,
        )
        if resample_image_process.returncode == 0:
            logger.info(
                "ResampleImage succeeded with the following output: "
                f"{resample_image_process.stdout}"
            )
        else:
            raise_error(
                msg="ResampleImage failed with the following error: "
                f"{resample_image_process.stdout}",
                klass=RuntimeError,
            )

        # Create a tempfile for warped output
        apply_transforms_out_path = tempdir / "input_warped.nii.gz"
        # Set antsApplyTransforms command
        apply_transforms_cmd = [
            "antsApplyTransforms",
            "-d 3",
            "-e 3",
            "-n LanczosWindowedSinc",
            f"-i {input_data['path'].resolve()}",
            # use resampled reference
            f"-r {resample_image_out_path.resolve()}",
            f"-t {warp_path.resolve()}",
            f"-o {apply_transforms_out_path.resolve()}",
        ]
        # Call antsApplyTransforms
        apply_transforms_cmd_str = " ".join(apply_transforms_cmd)
        logger.info(
            "antsApplyTransforms command to be executed: "
            f"{apply_transforms_cmd_str}"
        )
        apply_transforms_process = subprocess.run(
            apply_transforms_cmd_str,  # string needed with shell=True
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,  # needed for respecting $PATH
            check=False,
        )
        if apply_transforms_process.returncode == 0:
            logger.info(
                "antsApplyTransforms succeeded with the following output: "
                f"{apply_transforms_process.stdout}"
            )
        else:
            raise_error(
                msg=(
                    "antsApplyTransforms failed with the following error: "
                    f"{apply_transforms_process.stdout}"
                ),
                klass=RuntimeError,
            )

        # Load nifti
        output_img = nib.load(apply_transforms_out_path)

        # Stupid casting
        output_img = cast("Nifti1Image", output_img)
        return output_img, resample_image_out_path

    def preprocess(
        self,
        input: Dict[str, Any],
        extra_input: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """Preprocess.

        Parameters
        ----------
        input : dict
            A single input from the Junifer Data object in which to preprocess.
        extra_input : dict, optional
            The other fields in the Junifer Data object. Must include the
            ``Warp`` and ``ref`` value's keys.

        Returns
        -------
        str
            The key to store the output in the Junifer Data object.
        dict
            The computed result as dictionary. This will be stored in the
            Junifer Data object under the key ``data`` of the data type.

        Raises
        ------
        ValueError
            If ``extra_input`` is None.

        """
        logger.debug("Warping via ANTs using antsApplyTransforms")
        # Check for extra inputs
        if extra_input is None:
            raise_error(
                f"No extra input provided, requires `Warp` and `{self.ref}` "
                "data types in particular."
            )
        # Retrieve data type info to warp
        to_warp_input = input
        # Retrieve data type info to use as reference
        ref_input = extra_input[self.ref]
        # Retrieve Warp data
        warp = extra_input["Warp"]
        # Replace original data with warped data and add resampled reference
        # path
        input["data"], input["reference_path"] = self._run_apply_transforms(
            input_data=to_warp_input,
            ref_path=ref_input["path"],
            warp_path=warp["path"],
        )
        # Use reference input's space as warped input's space
        input["space"] = ref_input["space"]
        return self.on, input
