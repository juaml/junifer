"""Provide class for smoothing."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from collections.abc import Sequence
from enum import Enum
from typing import Any, ClassVar, Literal, Optional

from ...api.decorators import register_preprocessor
from ...datagrabber import DataType
from ...typing import ConditionalDependencies
from ..base import BasePreprocessor, logger
from ._afni_smoothing import AFNISmoothing
from ._fsl_smoothing import FSLSmoothing
from ._nilearn_smoothing import NilearnSmoothing


__all__ = ["Smoothing", "SmoothingImpl"]


class SmoothingImpl(str, Enum):
    """Accepted smoothing implementations.

    * ``nilearn`` : :func:`nilearn.image.smooth_img`
    * ``afni`` : AFNI's ``3dBlurToFWHM``
    * ``fsl`` : FSL SUSAN's ``susan``

    """

    nilearn = "nilearn"
    afni = "afni"
    fsl = "fsl"


@register_preprocessor
class Smoothing(BasePreprocessor):
    """Class for smoothing.

    Parameters
    ----------
    using : :enum:`.SmoothingImpl`
    on : list of {``DataType.T1w``, ``DataType.T2w``, ``DataType.BOLD``}
        The data type(s) to apply smoothing to.
    smoothing_params : dict, optional
        Extra parameters for smoothing as a dictionary (default None).
        If ``using=SmoothingImpl.nilearn``, then the valid keys are:

        * ``fmhw`` : scalar, ``numpy.ndarray``, tuple or list of scalar, \
                     "fast" or None
            Smoothing strength, as a full-width at half maximum, in
            millimeters:

            - If nonzero scalar, width is identical in all 3 directions.
            - If ``numpy.ndarray``, tuple, or list, it must have 3 elements,
              giving the FWHM along each axis. If any of the elements is 0 or
              None, smoothing is not performed along that axis.
            - If ``"fast"``, a fast smoothing will be performed with a filter
              ``[0.2, 1, 0.2]`` in each direction and a normalisation to
              preserve the local average value.
            - If None, no filtering is performed (useful when just removal of
              non-finite values is needed).

        else if ``using=SmoothingImpl.afni``, then the valid keys are:

        * ``fwhm`` : int or float
            Smooth until the value. AFNI estimates the smoothing and then
            applies smoothing to reach ``fwhm``.

        else if ``using=SmoothingImpl.fsl``, then the valid keys are:

        * ``brightness_threshold`` : float
            Threshold to discriminate between noise and the underlying image.
            The value should be set greater than the noise level and less than
            the contrast of the underlying image.
        * ``fwhm`` : float
            Spatial extent of smoothing.

    """

    _CONDITIONAL_DEPENDENCIES: ClassVar[ConditionalDependencies] = [
        {
            "using": SmoothingImpl.nilearn,
            "depends_on": [NilearnSmoothing],
        },
        {
            "using": SmoothingImpl.afni,
            "depends_on": [AFNISmoothing],
        },
        {
            "using": SmoothingImpl.fsl,
            "depends_on": [FSLSmoothing],
        },
    ]
    _VALID_DATA_TYPES: ClassVar[Sequence[DataType]] = [
        DataType.T1w,
        DataType.T2w,
        DataType.BOLD,
    ]

    using: SmoothingImpl
    on: list[Literal[DataType.T1w, DataType.T2w, DataType.BOLD]]
    smoothing_params: Optional[dict] = None

    def validate_preprocessor_params(self) -> None:
        """Run extra logical validation for preprocessor."""
        self.smoothing_params = (
            self.smoothing_params if self.smoothing_params is not None else {}
        )

    def preprocess(
        self,
        input: dict[str, Any],
        extra_input: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
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

        """
        logger.debug("Smoothing")

        # Conditional preprocessor
        if self.using == "nilearn":
            preprocessor = NilearnSmoothing()
        elif self.using == "afni":
            preprocessor = AFNISmoothing()
        elif self.using == "fsl":
            preprocessor = FSLSmoothing()
        # Smooth
        input = preprocessor.preprocess(
            input=input,
            **self.smoothing_params,
        )

        return input
