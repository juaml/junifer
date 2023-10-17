"""Provide class for warping via FSL FLIRT."""

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


class _ApplyWarper(BasePreprocessor):
    """Class for warping NIfTI images via FSL FLIRT.

    Wraps FSL FLIRT ``applywarp``.

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
            "name": "fsl",
            "optional": False,
            "commands": ["applywarp"],
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

    def _run_applywarp(
        self,
        input_data: Dict,
        ref_path: Path,
        warp_path: Path,
    ) -> Tuple["Nifti1Image", Path]:
        """Run ``applywarp``.

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
            If FSL commands fail.

        """
        # Get the min of the voxel sizes from input and use it as the
        # resolution
        resolution = np.min(input_data["data"].header.get_zooms()[:3])

        # Create element-specific tempdir for storing post-warping assets
        tempdir = WorkDirManager().get_element_tempdir(prefix="applywarp")

        # Create a tempfile for resampled reference output
        flirt_out_path = tempdir / "reference_resampled.nii.gz"
        # Set flirt command
        flirt_cmd = [
            "flirt",
            "-interp spline",
            f"-in {ref_path.resolve()}",
            f"-ref {ref_path.resolve()}",
            f"-applyisoxfm {resolution}",
            f"-out {flirt_out_path.resolve()}",
        ]
        # Call flirt
        flirt_cmd_str = " ".join(flirt_cmd)
        logger.info(f"flirt command to be executed: {flirt_cmd_str}")
        flirt_process = subprocess.run(
            flirt_cmd_str,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,  # needed for respecting $PATH
            check=False,
        )
        if flirt_process.returncode == 0:
            logger.info(
                "flirt succeeded with the following output: "
                f"{flirt_process.stdout}"
            )
        else:
            raise_error(
                msg="flirt failed with the following error: "
                f"{flirt_process.stdout}",
                klass=RuntimeError,
            )

        # TODO(synchon): Modify reference or not?

        # Create a tempfile for warped output
        applywarp_out_path = tempdir / "input_warped.nii.gz"
        # Set applywarp command
        applywarp_cmd = [
            "applywarp",
            "--interp=spline",
            f"-i {input_data['path'].resolve()}",
            f"-r {flirt_out_path.resolve()}",  # use resampled reference
            f"-w {warp_path.resolve()}",
            f"-o {applywarp_out_path.resolve()}",
        ]
        # Call applywarp
        applywarp_cmd_str = " ".join(applywarp_cmd)
        logger.info(f"applywarp command to be executed: {applywarp_cmd_str}")
        applywarp_process = subprocess.run(
            applywarp_cmd_str,  # string needed with shell=True
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,  # needed for respecting $PATH
            check=False,
        )
        if applywarp_process.returncode == 0:
            logger.info(
                "applywarp succeeded with the following output: "
                f"{applywarp_process.stdout}"
            )
        else:
            raise_error(
                msg="applywarp failed with the following error: "
                f"{applywarp_process.stdout}",
                klass=RuntimeError,
            )

        # Load nifti
        output_img = nib.load(applywarp_out_path)

        # Stupid casting
        output_img = cast("Nifti1Image", output_img)
        return output_img, flirt_out_path

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
        logger.debug("Warping via FSL using ApplyWarper")
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
        input["data"], input["reference_path"] = self._run_applywarp(
            input_data=to_warp_input,
            ref_path=ref_input["path"],
            warp_path=warp["path"],
        )
        # Use reference input's space as warped input's space
        input["space"] = ref_input["space"]
        return self.on, input
