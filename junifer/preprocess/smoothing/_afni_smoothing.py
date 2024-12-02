"""Provide class for smoothing via AFNI."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import (
    Any,
    ClassVar,
    Union,
)

import nibabel as nib

from ...pipeline import WorkDirManager
from ...typing import Dependencies, ExternalDependencies
from ...utils import logger, run_ext_cmd


__all__ = ["AFNISmoothing"]


class AFNISmoothing:
    """Class for smoothing via AFNI.

    This class uses AFNI's 3dBlurToFWHM.

    """

    _EXT_DEPENDENCIES: ClassVar[ExternalDependencies] = [
        {
            "name": "afni",
            "commands": ["3dBlurToFWHM"],
        },
    ]

    _DEPENDENCIES: ClassVar[Dependencies] = {"nibabel"}

    def preprocess(
        self,
        input: dict[str, Any],
        fwhm: Union[int, float],
    ) -> dict[str, Any]:
        """Preprocess using AFNI.

        Parameters
        ----------
        input : dict
            A single input from the Junifer Data object in which to preprocess.
        fwhm : int or float
            Smooth until the value. AFNI estimates the smoothing and then
            applies smoothing to reach ``fwhm``.

        Returns
        -------
        dict
            The ``input`` dictionary with updated values.

        Notes
        -----
        For more information on ``3dBlurToFWHM``, check:
        https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dBlurToFWHM.html

        As the process also depends on the conversion of AFNI files to NIfTI
        via AFNI's ``3dAFNItoNIFTI``, the help for that can be found at:
        https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dAFNItoNIFTI.html

        """
        logger.info("Smoothing using AFNI")

        # Create element-scoped tempdir so that the output is
        # available later as nibabel stores file path reference for
        # loading on computation
        element_tempdir = WorkDirManager().get_element_tempdir(
            prefix="afni_smoothing"
        )

        # Set 3dBlurToFWHM command
        blur_out_path_prefix = element_tempdir / "blur"
        blur_cmd = [
            "3dBlurToFWHM",
            f"-input {input['path'].resolve()}",
            f"-prefix {blur_out_path_prefix.resolve()}",
            "-automask",
            f"-FWHM {fwhm}",
        ]
        # Call 3dBlurToFWHM
        run_ext_cmd(name="3dBlurToFWHM", cmd=blur_cmd)

        # Read header to get output suffix
        header = input["data"].header
        sform_code = header.get_sform(coded=True)[1]
        if sform_code == 4:
            output_suffix = "tlrc"
        else:
            output_suffix = "orig"

        # Convert afni to nifti
        blur_nifti_out_path = (
            element_tempdir / "smoothed_data.nii"  # needs to be .nii
        )
        convert_cmd = [
            "3dAFNItoNIFTI",
            f"-prefix {blur_nifti_out_path.resolve()}",
            f"{blur_out_path_prefix}+{output_suffix}.BRIK",
        ]
        # Call 3dAFNItoNIFTI
        run_ext_cmd(name="3dAFNItoNIFTI", cmd=convert_cmd)

        logger.debug("Updating smoothed data")
        input.update(
            {
                # Update path to sync with "data"
                "path": blur_nifti_out_path,
                # Load nifti
                "data": nib.load(blur_nifti_out_path),
            }
        )

        return input
