"""Provide class for smoothing via FSL."""

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


__all__ = ["FSLSmoothing"]


class FSLSmoothing:
    """Class for smoothing via FSL.

    This class uses FSL's susan.

    """

    _EXT_DEPENDENCIES: ClassVar[List[Dict[str, Union[str, List[str]]]]] = [
        {
            "name": "fsl",
            "commands": ["susan"],
        },
    ]

    _DEPENDENCIES: ClassVar[Set[str]] = {"nibabel"}

    def preprocess(
        self,
        data: "Nifti1Image",
        brightness_threshold: float,
        fwhm: float,
    ) -> "Nifti1Image":
        """Preprocess using FSL.

        Parameters
        ----------
        data : Niimg-like object
            Image(s) to preprocess.
        brightness_threshold : float
            Threshold to discriminate between noise and the underlying image.
            The value should be set greater than the noise level and less than
            the contrast of the underlying image.
        fwhm : float
            Spatial extent of smoothing.

        Returns
        -------
        Niimg-like object
            The preprocessed image(s).

        Notes
        -----
        For more information on ``SUSAN``, check [1]_

        References
        ----------
        .. [1] Smith, S.M. and Brady, J.M. (1997).
               SUSAN - a new approach to low level image processing.
               International Journal of Computer Vision, Volume 23(1),
               Pages 45-78.

        """
        logger.info("Smoothing using FSL")

        # Create component-scoped tempdir
        tempdir = WorkDirManager().get_tempdir(prefix="fsl_smoothing")

        # Save target data to a component-scoped tempfile
        nifti_in_file_path = tempdir / "input.nii.gz"
        nib.save(data, nifti_in_file_path)

        # Create element-scoped tempdir so that the output is
        # available later as nibabel stores file path reference for
        # loading on computation
        element_tempdir = WorkDirManager().get_element_tempdir(
            prefix="fsl_susan"
        )
        susan_out_path = element_tempdir / "output.nii.gz"
        # Set susan command
        susan_cmd = [
            "susan",
            f"{nifti_in_file_path.resolve()}",
            f"{brightness_threshold}",
            f"{fwhm}",
            "3",  # dimension
            "1",  # use median when no neighbourhood is found
            "0",  # use input image to find USAN
            f"{susan_out_path.resolve()}",
        ]
        # Call susan
        run_ext_cmd(name="susan", cmd=susan_cmd)

        # Load nifti
        output_data = nib.load(susan_out_path)

        # Delete tempdir
        WorkDirManager().delete_tempdir(tempdir)

        return output_data  # type: ignore
