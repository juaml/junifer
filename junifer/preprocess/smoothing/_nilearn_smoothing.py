"""Provide class for smoothing via nilearn."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import (
    Any,
    ClassVar,
    Literal,
    Union,
)

import nibabel as nib
from nilearn import image as nimg
from numpy.typing import ArrayLike

from ...pipeline import WorkDirManager
from ...typing import Dependencies
from ...utils import logger


__all__ = ["NilearnSmoothing"]


class NilearnSmoothing:
    """Class for smoothing via nilearn.

    This class uses :func:`nilearn.image.smooth_img` to smooth image(s).

    """

    _DEPENDENCIES: ClassVar[Dependencies] = {"nilearn"}

    def preprocess(
        self,
        input: dict[str, Any],
        fwhm: Union[int, float, ArrayLike, Literal["fast"], None],
    ) -> dict[str, Any]:
        """Preprocess using nilearn.

        Parameters
        ----------
        input : dict
            A single input from the Junifer Data object in which to preprocess.
        fwhm : scalar, ``numpy.ndarray``, tuple or list of scalar, "fast" or \
               None
            Smoothing strength, as a full-width at half maximum, in
            millimeters:

            * If nonzero scalar, width is identical in all 3 directions.
            * If ``numpy.ndarray``, tuple, or list, it must have 3 elements,
              giving the FWHM along each axis. If any of the elements is 0 or
              None, smoothing is not performed along that axis.
            * If ``"fast"``, a fast smoothing will be performed with a filter
              ``[0.2, 1, 0.2]`` in each direction and a normalisation to
              preserve the local average value.
            * If None, no filtering is performed (useful when just removal of
              non-finite values is needed).

        Returns
        -------
        dict
            The ``input`` dictionary with updated values.

        """
        logger.info("Smoothing using nilearn")

        # Create element-scoped tempdir so that the output is
        # available later as nibabel stores file path reference for
        # loading on computation
        element_tempdir = WorkDirManager().get_element_tempdir(
            prefix="nilearn_smoothing"
        )

        smoothed_img = nimg.smooth_img(imgs=input["data"], fwhm=fwhm)

        # Save smoothed output
        smoothed_img_path = element_tempdir / "smoothed_data.nii.gz"
        nib.save(smoothed_img, smoothed_img_path)

        logger.debug("Updating smoothed data")
        input.update(
            {
                # Update path to sync with "data"
                "path": smoothed_img_path,
                "data": smoothed_img,
            }
        )

        return input
