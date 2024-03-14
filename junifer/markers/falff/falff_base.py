"""Provide base class for ALFF / fALFF."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Kaustubh R. Patil <k.patil@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    Union,
)

from ...utils.logging import logger, raise_error
from ..base import BaseMarker
from ._afni_falff import AFNIALFF
from ._junifer_falff import JuniferALFF


if TYPE_CHECKING:
    from nibabel import Nifti1Image


class ALFFBase(BaseMarker):
    """Base class for (fractional) Amplitude Low Frequency Fluctuation.

    Parameters
    ----------
    fractional : bool
        Whether to compute fractional ALFF.
    highpass : positive float
        Highpass cutoff frequency.
    lowpass : positive float
        Lowpass cutoff frequency.
    using : {"junifer", "afni"}
        Implementation to use for computing ALFF:

        * "junifer" : Use ``junifer``'s own ALFF implementation
        * "afni" : Use AFNI's ``3dRSFC``

    tr : positive float, optional
        The Repetition Time of the BOLD data. If None, will extract
        the TR from NIfTI header (default None).
    name : str, optional
        The name of the marker. If None, it will use the class name
        (default None).

    Notes
    -----
    The ``tr`` parameter is crucial for the correctness of fALFF/ALFF
    computation. If a dataset is correctly preprocessed, the ``tr`` should be
    extracted from the NIfTI without any issue. However, it has been
    reported that some preprocessed data might not have the correct ``tr`` in
    the NIfTI header.

    Raises
    ------
    ValueError
        If ``highpass`` is not positive or zero or
        if ``lowpass`` is not positive or
        if ``highpass`` is higher than ``lowpass`` or
        if ``using`` is invalid.

    """

    _CONDITIONAL_DEPENDENCIES: ClassVar[List[Dict[str, Union[str, Type]]]] = [
        {
            "using": "afni",
            "depends_on": AFNIALFF,
        },
        {
            "using": "junifer",
            "depends_on": JuniferALFF,
        },
    ]

    def __init__(
        self,
        fractional: bool,
        highpass: float,
        lowpass: float,
        using: str,
        tr: Optional[float] = None,
        name: Optional[str] = None,
    ) -> None:
        if highpass < 0:
            raise_error("Highpass must be positive or 0")
        if lowpass <= 0:
            raise_error("Lowpass must be positive")
        if highpass >= lowpass:
            raise_error("Highpass must be lower than lowpass")
        self.highpass = highpass
        self.lowpass = lowpass
        # Validate `using` parameter
        valid_using = [dep["using"] for dep in self._CONDITIONAL_DEPENDENCIES]
        if using not in valid_using:
            raise_error(
                f"Invalid value for `using`, should be one of: {valid_using}"
            )
        self.using = using
        self.tr = tr
        self.fractional = fractional

        # Create a name based on the class name if none is provided
        if name is None:
            suffix = "_fractional" if fractional else ""
            name = f"{self.__class__.__name__}{suffix}"
        super().__init__(on="BOLD", name=name)

    def get_valid_inputs(self) -> List[str]:
        """Get valid data types for input.

        Returns
        -------
        list of str
            The list of data types that can be used as input for this marker.

        """
        return ["BOLD"]

    def get_output_type(self, input_type: str) -> str:
        """Get output type.

        Parameters
        ----------
        input_type : str
            The data type input to the marker.

        Returns
        -------
        str
            The storage type output by the marker.

        """
        return "vector"

    def _compute(
        self,
        input_data: Dict[str, Any],
    ) -> Tuple["Nifti1Image", Path]:
        """Compute ALFF and fALFF.

        Parameters
        ----------
        input_data : dict
            The input to the marker.
        extra_input : dict, optional
            The other fields in the pipeline data object (default None).

        Returns
        -------
        Niimg-like object
            The ALFF / fALFF as NIfTI.
        pathlib.Path
            The path to the ALFF / fALFF as NIfTI.

        """
        logger.debug("Calculating ALFF and fALFF")

        # Conditional estimator
        if self.using == "afni":
            estimator = AFNIALFF()
        elif self.using == "junifer":
            estimator = JuniferALFF()
        # Compute ALFF + fALFF
        alff, falff, alff_path, falff_path = estimator.compute(  # type: ignore
            data=input_data["data"],
            highpass=self.highpass,
            lowpass=self.lowpass,
            tr=self.tr,
        )

        # If the input data space is native already, the original path should
        # be propagated down as it might be required for transforming
        # parcellation / coordinates to native space, else the
        # path should be passed for use later if required.
        # TODO(synchon): will be taken care in #292
        if input_data["space"] == "native" and self.fractional:
            return falff, input_data["path"]
        elif input_data["space"] == "native" and not self.fractional:
            return alff, input_data["path"]
        elif input_data["space"] != "native" and self.fractional:
            return falff, falff_path
        else:
            return alff, alff_path
