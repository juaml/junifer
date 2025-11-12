"""Provide base class for ALFF / fALFF."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Kaustubh R. Patil <k.patil@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from enum import Enum
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Literal,
    Optional,
    Union,
)

from pydantic import PositiveFloat

from ...datagrabber import DataType
from ...storage import StorageType
from ...typing import ConditionalDependencies, MarkerInOutMappings
from ...utils.logging import logger
from ..base import BaseMarker
from ._afni_falff import AFNIALFF
from ._junifer_falff import JuniferALFF


if TYPE_CHECKING:
    from nibabel.nifti1 import Nifti1Image


__all__ = ["ALFFBase", "ALFFImpl"]


class ALFFImpl(str, Enum):
    """Accepted ALFF implementations.

    * ``junifer`` : ``junifer``'s ALFF
    * ``afni`` : AFNI's ``3dRSFC``

    """

    junifer = "junifer"
    afni = "afni"


class ALFFBase(BaseMarker):
    """Base class for (fractional) Amplitude Low Frequency Fluctuation.

    Parameters
    ----------
    using : :enum:`.ALFFImpl`
    highpass : positive float, optional
        Highpass cutoff frequency (default 0.01).
    lowpass : positive float, optional
        Lowpass cutoff frequency (default 0.1).
    tr : positive float, optional
        The repetition time of the BOLD data.
        If None, will extract the TR from NIfTI header (default None).
    agg_method : str, optional
        The aggregation function to use.
        See :func:`.get_aggfunc_by_name` for options
        (default "mean").
    agg_method_params : dict or None, optional
        The parameters to pass to the aggregation function.
        See :func:`.get_aggfunc_by_name` for options (default None).
    masks : list of dict or str, or None, optional
        The specification of the masks to apply to regions before extracting
        signals. Check :ref:`Using Masks <using_masks>` for more details.
        If None, will not apply any mask (default None).
    name : str or None, optional
        The name of the marker.
        If None, it will use the class name (default None).

    Notes
    -----
    The ``tr`` parameter is crucial for the correctness of fALFF/ALFF
    computation. If a dataset is correctly preprocessed, the ``tr`` should be
    extracted from the NIfTI without any issue. However, it has been
    reported that some preprocessed data might not have the correct ``tr`` in
    the NIfTI header.

    """

    _CONDITIONAL_DEPENDENCIES: ClassVar[ConditionalDependencies] = [
        {
            "depends_on": AFNIALFF,
            "using": ALFFImpl.afni,
        },
        {
            "depends_on": JuniferALFF,
            "using": ALFFImpl.junifer,
        },
    ]

    _MARKER_INOUT_MAPPINGS: ClassVar[MarkerInOutMappings] = {
        DataType.BOLD: {
            "alff": StorageType.Vector,
            "falff": StorageType.Vector,
        },
    }

    using: ALFFImpl
    highpass: PositiveFloat = 0.01
    lowpass: PositiveFloat = 0.1
    tr: Optional[PositiveFloat] = None
    agg_method: str = "mean"
    agg_method_params: Optional[dict] = None
    masks: Optional[list[Union[dict, str]]] = None
    on: list[Literal[DataType.BOLD]] = [DataType.BOLD]  # noqa: RUF012

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
