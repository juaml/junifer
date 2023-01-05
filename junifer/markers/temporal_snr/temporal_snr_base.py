"""Provide abstract base class for temporal signal-to-noise ratio (tSNR)."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL


from abc import abstractmethod
from typing import Any, Dict, List, Optional

from ...utils import raise_error
from ..base import BaseMarker
from ..utils import _voxelwise_tsnr


class TemporalSNRBase(BaseMarker):
    """Abstract base class for temporal SNR markers.

    Parameters
    ----------
    agg_method : str, optional
        The method to perform aggregation using. Check valid options in
        :func:`junifer.stats.get_aggfunc_by_name` (default "mean").
    agg_method_params : dict, optional
        Parameters to pass to the aggregation function. Check valid options in
        :func:`junifer.stats.get_aggfunc_by_name` (default None).
    mask : str, optional
        The name of the mask to apply to regions before extracting signals.
        Check valid options by calling :func:`junifer.data.masks.list_masks`
        (default None).
    name : str, optional
        The name of the marker. If None, will use the class name (default
        None).

    """

    _DEPENDENCIES = {"nilearn"}

    def __init__(
        self,
        agg_method: str = "mean",
        agg_method_params: Optional[Dict] = None,
        mask: Optional[str] = None,
        name: Optional[str] = None,
    ) -> None:
        self.agg_method = agg_method
        self.agg_method_params = agg_method_params

        self.mask = mask
        super().__init__(on="BOLD", name=name)

    @abstractmethod
    def aggregate(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Perform aggregation."""
        raise_error(
            msg="Concrete classes need to implement aggregate().",
            klass=NotImplementedError,
        )

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
        return "table"

    def compute(
        self,
        input: Dict[str, Any],
        extra_input: Optional[Dict] = None,
    ) -> Dict:
        """Compute.

        Parameters
        ----------
        input : dict
            A single input from the pipeline data object in which to compute
            the marker.
        extra_input : dict, optional
            The other fields in the pipeline data object. Useful for accessing
            other data kind that needs to be used in the computation.

        Returns
        -------
        dict
            The computed result as dictionary. The following keys will be
            included in the dictionary:

            * ``data`` : functional connectivity matrix as a ``numpy.ndarray``.
            * ``columns`` : the column labels for the computed values as a list

        """
        # calculate voxelwise temporal snr in an image
        input = _voxelwise_tsnr(input)

        # Perform necessary aggregation and return
        return self.aggregate(input)
