"""Provide class for smoothing via FSL."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import (
    Any,
    ClassVar,
)

import nibabel as nib

from ...pipeline import WorkDirManager
from ...typing import Dependencies, ExternalDependencies
from ...utils import logger, run_ext_cmd


__all__ = ["FSLSmoothing"]


class FSLSmoothing:
    """Class for smoothing via FSL.

    This class uses FSL's susan.

    """

    _EXT_DEPENDENCIES: ClassVar[ExternalDependencies] = [
        {
            "name": "fsl",
            "commands": ["susan"],
        },
    ]

    _DEPENDENCIES: ClassVar[Dependencies] = {"nibabel"}

    def preprocess(
        self,
        input: dict[str, Any],
        brightness_threshold: float,
        fwhm: float,
    ) -> dict[str, Any]:
        """Preprocess using FSL.

        Parameters
        ----------
        input : dict
            A single input from the Junifer Data object in which to preprocess.
        brightness_threshold : float
            Threshold to discriminate between noise and the underlying image.
            The value should be set greater than the noise level and less than
            the contrast of the underlying image.
        fwhm : float
            Spatial extent of smoothing.

        Returns
        -------
        dict
            The ``input`` dictionary with updated values.

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

        # Create element-scoped tempdir so that the output is
        # available later as nibabel stores file path reference for
        # loading on computation
        element_tempdir = WorkDirManager().get_element_tempdir(
            prefix="fsl_susan"
        )
        susan_out_path = element_tempdir / "smoothed_data.nii.gz"
        # Set susan command
        susan_cmd = [
            "susan",
            f"{input['path'].resolve()}",
            f"{brightness_threshold}",
            f"{fwhm}",
            "3",  # dimension
            "1",  # use median when no neighbourhood is found
            "0",  # use input image to find USAN
            f"{susan_out_path.resolve()}",
        ]
        # Call susan
        run_ext_cmd(name="susan", cmd=susan_cmd)

        logger.debug("Updating smoothed data")
        input.update(
            {
                # Update path to sync with "data"
                "path": susan_out_path,
                # Load nifti
                "data": nib.load(susan_out_path),
            }
        )

        return input
