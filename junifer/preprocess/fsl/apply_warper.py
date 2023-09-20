"""Provide class for warping via FSL FLIRT."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import subprocess
import tempfile
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

from ...api.decorators import register_preprocessor
from ...utils import logger, raise_error
from ..base import BasePreprocessor


if TYPE_CHECKING:
    from nibabel import Nifti1Image


@register_preprocessor
class ApplyWarper(BasePreprocessor):
    """Class for warping NIfTI images via FSL FLIRT.

    Wraps FSL FLIRT ``applywarp``.

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

    def __init__(self) -> None:
        """Initialize the class."""
        super().__init__(on="BOLD")

    def get_valid_inputs(self) -> List[str]:
        """Get valid data types for input.

        Returns
        -------
        list of str
            The list of data types that can be used as input for this
            preprocessor.

        """
        return ["BOLD", "T1w", "Warp"]

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
        input_path: Path,
        ref_path: Path,
        warp_path: Path,
    ) -> "Nifti1Image":
        """Run ``applywarp``.

        Parameters
        ----------
        input_path : pathlib.Path
            The path to the input file.
        ref_path : pathlib.Path
            The path to the reference file.
        warp_path : pathlib.Path
            The path to the warp file.

        Returns
        -------
        Niimg-like object

        """
        # Create a tempfile for warped BOLD output
        applywarp_out_path = Path(tempfile.mkdtemp()) / "bold_warped.nii.gz"
        # Set applywarp command
        applywarp_cmd = [
            "applywarp",
            "--interp=spline",
            f"-i {input_path.resolve()}",
            f"-r {ref_path.resolve()}",
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
        # Delete file
        applywarp_out_path.unlink()

        # Stupid casting
        output_img = cast("Nifti1Image", output_img)
        return output_img

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
            ``T1w`` and ``Warp`` keys.

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
        # Check for extra inputs
        if extra_input is None:
            raise_error(
                "No extra input provided, requires `T1w` and `Warp` data "
                "types in particular."
            )
        # Retrieve BOLD data
        bold = input
        # Retrieve T1w data
        t1w = extra_input["T1w"]
        # Retrieve Warp data
        warp = extra_input["Warp"]
        # Replace original BOLD data with warped BOLD data
        input["data"] = self._run_applywarp(
            input_path=bold["path"],
            ref_path=t1w["path"],
            warp_path=warp["path"],
        )
        return "BOLD", input
