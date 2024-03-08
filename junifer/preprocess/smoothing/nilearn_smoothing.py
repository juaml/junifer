"""Provide class for smoothing via nilearn."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import (
    Any,
    ClassVar,
    Dict,
    List,
    Literal,
    Optional,
    Set,
    Tuple,
    Union,
)

from nilearn import image as nimg
from numpy.typing import ArrayLike

from ...api.decorators import register_preprocessor
from ...utils import logger
from .smoothing_base import SmoothingBase


__all__ = ["NilearnSmoothing"]


@register_preprocessor
class NilearnSmoothing(SmoothingBase):
    """Class for smoothing via nilearn.

    Parameters
    ----------
    fwhm : scalar, ``numpy.ndarray``, tuple or list of scalar, "fast" or None
        Smoothing strength, as a full-width at half maximum, in millimeters:

        * If nonzero scalar, width is identical in all 3 directions.
        * If ``numpy.ndarray``, tuple, or list, it must have 3 elements, giving
          the FWHM along each axis. If any of the elements is 0 or None,
          smoothing is not performed along that axis.
        * If ``"fast"``, a fast smoothing will be performed with a filter
          ``[0.2, 1, 0.2]`` in each direction and a normalisation to preserve
          the local average value.
        * If None, no filtering is performed (useful when just removal of
          non-finite values is needed).

    on : {"T1w", "T2w", "BOLD"} or list of the options or None
        The data type to apply smoothing to. If None, will apply to all
        available data types (default None).

    """

    _DEPENDENCIES: ClassVar[Set[str]] = {"nilearn"}

    def __init__(
        self,
        fwhm: Union[int, float, ArrayLike, Literal["fast"], None],
        on: Optional[Union[List[str], str]] = None,
    ) -> None:
        """Initialize the class."""
        self.fwhm = fwhm
        super().__init__(on=on)

    def preprocess(
        self,
        input: Dict[str, Any],
        extra_input: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], Optional[Dict[str, Dict[str, Any]]]]:
        """Preprocess.

        Parameters
        ----------
        input : dict
            The input from the Junifer Data object.
        extra_input : dict, optional
            The other fields in the Junifer Data object.

        Returns
        -------
        dict
            The computed result as dictionary.
        None
            Extra "helper" data types as dictionary to add to the Junifer Data
            object.

        """
        logger.info("Smoothing using NilearnSmoothing")
        input["data"] = nimg.smooth_img(imgs=input["data"], fwhm=self.fwhm)
        return input, None
