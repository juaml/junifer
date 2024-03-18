"""Provide class for smoothing via nilearn."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import (
    TYPE_CHECKING,
    ClassVar,
    Literal,
    Set,
    Union,
)

from nilearn import image as nimg
from numpy.typing import ArrayLike

from ...utils import logger


if TYPE_CHECKING:
    from nibabel import Nifti1Image


__all__ = ["NilearnSmoothing"]


class NilearnSmoothing:
    """Class for smoothing via nilearn.

    This class uses :func:`nilearn.image.smooth_img` to smooth image(s).

    """

    _DEPENDENCIES: ClassVar[Set[str]] = {"nilearn"}

    def preprocess(
        self,
        data: "Nifti1Image",
        fwhm: Union[int, float, ArrayLike, Literal["fast"], None],
    ) -> "Nifti1Image":
        """Preprocess using nilearn.

        Parameters
        ----------
        data : Niimg-like object
            Image(s) to preprocess.
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
        Niimg-like object
            The preprocessed image(s).

        """
        logger.info("Smoothing using nilearn")
        return nimg.smooth_img(imgs=data, fwhm=fwhm)  # type: ignore
