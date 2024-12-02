"""Provide class for smoothing."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Any, ClassVar, Optional, Union

from ...api.decorators import register_preprocessor
from ...typing import ConditionalDependencies
from ...utils import logger, raise_error
from ..base import BasePreprocessor
from ._afni_smoothing import AFNISmoothing
from ._fsl_smoothing import FSLSmoothing
from ._nilearn_smoothing import NilearnSmoothing


__all__ = ["Smoothing"]


@register_preprocessor
class Smoothing(BasePreprocessor):
    """Class for smoothing.

    Parameters
    ----------
    using : {"nilearn", "afni", "fsl"}
        Implementation to use for smoothing:

        * "nilearn" : Use :func:`nilearn.image.smooth_img`
        * "afni" : Use AFNI's ``3dBlurToFWHM``
        * "fsl" : Use FSL SUSAN's ``susan``

    on : {"T1w", "T2w", "BOLD"} or list of the options
        The data type to apply smoothing to.
    smoothing_params : dict, optional
        Extra parameters for smoothing as a dictionary (default None).
        If ``using="nilearn"``, then the valid keys are:

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

        else if ``using="afni"``, then the valid keys are:

        * ``fwhm`` : int or float
            Smooth until the value. AFNI estimates the smoothing and then
            applies smoothing to reach ``fwhm``.

        else if ``using="fsl"``, then the valid keys are:

        * ``brightness_threshold`` : float
            Threshold to discriminate between noise and the underlying image.
            The value should be set greater than the noise level and less than
            the contrast of the underlying image.
        * ``fwhm`` : float
            Spatial extent of smoothing.

    """

    _CONDITIONAL_DEPENDENCIES: ClassVar[ConditionalDependencies] = [
        {
            "using": "nilearn",
            "depends_on": NilearnSmoothing,
        },
        {
            "using": "afni",
            "depends_on": AFNISmoothing,
        },
        {
            "using": "fsl",
            "depends_on": FSLSmoothing,
        },
    ]

    def __init__(
        self,
        using: str,
        on: Union[list[str], str],
        smoothing_params: Optional[dict] = None,
    ) -> None:
        """Initialize the class."""
        # Validate `using` parameter
        valid_using = [dep["using"] for dep in self._CONDITIONAL_DEPENDENCIES]
        if using not in valid_using:
            raise_error(
                f"Invalid value for `using`, should be one of: {valid_using}"
            )
        self.using = using
        self.smoothing_params = (
            smoothing_params if smoothing_params is not None else {}
        )
        super().__init__(on=on)

    def get_valid_inputs(self) -> list[str]:
        """Get valid data types for input.

        Returns
        -------
        list of str
            The list of data types that can be used as input for this
            preprocessor.

        """
        return ["T1w", "T2w", "BOLD"]

    def get_output_type(self, input_type: str) -> str:
        """Get output type.

        Parameters
        ----------
        input_type : str
            The data type input to the preprocessor.

        Returns
        -------
        str
            The data type output by the preprocessor.

        """
        # Does not add any new keys
        return input_type

    def preprocess(
        self,
        input: dict[str, Any],
        extra_input: Optional[dict[str, Any]] = None,
    ) -> tuple[dict[str, Any], Optional[dict[str, dict[str, Any]]]]:
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

        return input, None
