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
    Optional,
)

from ...typing import ConditionalDependencies, MarkerInOutMappings
from ...utils.logging import logger, raise_error
from ..base import BaseMarker
from ._afni_falff import AFNIALFF
from ._junifer_falff import JuniferALFF


if TYPE_CHECKING:
    from nibabel.nifti1 import Nifti1Image


__all__ = ["ALFFBase"]


class ALFFBase(BaseMarker):
    """Base class for (fractional) Amplitude Low Frequency Fluctuation.

    Parameters
    ----------
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

    _CONDITIONAL_DEPENDENCIES: ClassVar[ConditionalDependencies] = [
        {
            "using": "afni",
            "depends_on": AFNIALFF,
        },
        {
            "using": "junifer",
            "depends_on": JuniferALFF,
        },
    ]

    _MARKER_INOUT_MAPPINGS: ClassVar[MarkerInOutMappings] = {
        "BOLD": {
            "alff": "vector",
            "falff": "vector",
        },
    }

    def __init__(
        self,
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
        super().__init__(on="BOLD", name=name)

    def _compute(
        self,
        input_data: dict[str, Any],
    ) -> tuple["Nifti1Image", "Nifti1Image", Path, Path]:
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
            The ALFF as NIfTI.
        Niimg-like object
            The fALFF as NIfTI.
        pathlib.Path
            The path to the ALFF as NIfTI.
        pathlib.Path
            The path to the fALFF as NIfTI.

        """
        logger.debug("Calculating ALFF and fALFF")

        # Conditional estimator
        if self.using == "afni":
            estimator = AFNIALFF()
        elif self.using == "junifer":
            estimator = JuniferALFF()
        # Compute ALFF + fALFF
        alff, falff, alff_path, falff_path = estimator.compute(  # type: ignore
            input_path=input_data["path"],
            highpass=self.highpass,
            lowpass=self.lowpass,
            tr=self.tr,
        )

        # If the input data space is native already, the original path should
        # be propagated down as it might be required for transforming
        # parcellation / coordinates to native space, else the
        # path should be passed for use later if required.
        # TODO(synchon): will be taken care in #292
        if input_data["space"] == "native":
            return alff, falff, input_data["path"], input_data["path"]
        else:
            return alff, falff, alff_path, falff_path
