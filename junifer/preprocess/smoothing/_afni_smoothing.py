"""Provide class for smoothing via AFNI."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import (
    TYPE_CHECKING,
    ClassVar,
    Dict,
    List,
    Set,
    Union,
)

import nibabel as nib

from ...pipeline import WorkDirManager
from ...utils import logger, run_ext_cmd


if TYPE_CHECKING:
    from nibabel import Nifti1Image


__all__ = ["AFNISmoothing"]


class AFNISmoothing:
    """Class for smoothing via AFNI.

    This class uses AFNI's 3dBlurToFWHM.

    """

    _EXT_DEPENDENCIES: ClassVar[List[Dict[str, Union[str, List[str]]]]] = [
        {
            "name": "afni",
            "commands": ["3dBlurToFWHM"],
        },
    ]

    _DEPENDENCIES: ClassVar[Set[str]] = {"nibabel"}

    def preprocess(
        self,
        data: "Nifti1Image",
        fwhm: Union[int, float],
    ) -> "Nifti1Image":
        """Preprocess using AFNI.

        Parameters
        ----------
        data : Niimg-like object
            Image(s) to preprocess.
        fwhm : int or float
            Smooth until the value. AFNI estimates the smoothing and then
            applies smoothing to reach ``fwhm``.

        Returns
        -------
        Niimg-like object
            The preprocessed image(s).

        Notes
        -----
        For more information on ``3dBlurToFWHM``, check:
        https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dBlurToFWHM.html

        As the process also depends on the conversion of AFNI files to NIfTI
        via AFNI's ``3dAFNItoNIFTI``, the help for that can be found at:
        https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dAFNItoNIFTI.html

        """
        logger.info("Smoothing using AFNI")

        # Create component-scoped tempdir
        tempdir = WorkDirManager().get_tempdir(prefix="afni_smoothing")

        # Save target data to a component-scoped tempfile
        nifti_in_file_path = tempdir / "input.nii"  # needs to be .nii
        nib.save(data, nifti_in_file_path)

        # Set 3dBlurToFWHM command
        blur_out_path_prefix = tempdir / "blur"
        blur_cmd = [
            "3dBlurToFWHM",
            f"-input {nifti_in_file_path.resolve()}",
            f"-prefix {blur_out_path_prefix.resolve()}",
            "-automask",
            f"-FWHM {fwhm}",
        ]
        # Call 3dBlurToFWHM
        run_ext_cmd(name="3dBlurToFWHM", cmd=blur_cmd)

        # Create element-scoped tempdir so that the blurred output is
        # available later as nibabel stores file path reference for
        # loading on computation
        element_tempdir = WorkDirManager().get_element_tempdir(
            prefix="afni_blur"
        )
        # Convert afni to nifti
        blur_afni_to_nifti_out_path = (
            element_tempdir / "output.nii"  # needs to be .nii
        )
        convert_cmd = [
            "3dAFNItoNIFTI",
            f"-prefix {blur_afni_to_nifti_out_path.resolve()}",
            f"{blur_out_path_prefix}+orig.BRIK",
        ]
        # Call 3dAFNItoNIFTI
        run_ext_cmd(name="3dAFNItoNIFTI", cmd=convert_cmd)

        # Load nifti
        output_data = nib.load(blur_afni_to_nifti_out_path)

        # Delete tempdir
        WorkDirManager().delete_tempdir(tempdir)

        return output_data  # type: ignore
