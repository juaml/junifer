"""Provide base class for complexity."""

# Authors: Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
# License: AGPL

from abc import abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Dict,
    List,
    Optional,
    Set,
    Union,
)

from ...utils import raise_error
from ..base import BaseMarker
from ..parcel_aggregation import ParcelAggregation


if TYPE_CHECKING:
    import numpy as np


class ComplexityBase(BaseMarker):
    """Base class for complexity computation.

    Parameters
    ----------
    parcellation : str or list of str
        The name(s) of the parcellation(s). Check valid options by calling
        :func:`junifer.data.parcellations.list_parcellations`.
    agg_method : str, optional
        The method to perform aggregation using. Check valid options in
        :func:`junifer.stats.get_aggfunc_by_name` (default "mean").
    agg_method_params : dict, optional
        Parameters to pass to the aggregation function. Check valid options in
        :func:`junifer.stats.get_aggfunc_by_name` (default None).
    masks : str, dict or list of dict or str, optional
        The specification of the masks to apply to regions before extracting
        signals. Check :ref:`Using Masks <using_masks>` for more details.
        If None, will not apply any mask (default None).
    name : str, optional
        The name of the marker. If None, it will use the class name
        (default None).

    """

    _DEPENDENCIES: ClassVar[Set[str]] = {"nilearn", "neurokit2"}

    def __init__(
        self,
        parcellation: Union[str, List[str]],
        agg_method: str = "mean",
        agg_method_params: Optional[Dict] = None,
        masks: Union[str, Dict, List[Union[Dict, str]], None] = None,
        name: Optional[str] = None,
    ) -> None:
        self.parcellation = parcellation
        self.agg_method = agg_method
        self.agg_method_params = agg_method_params
        self.masks = masks
        super().__init__(on="BOLD", name=name)

    @abstractmethod
    def compute_complexity(
        self,
        extracted_bold_values: "np.ndarray",
    ) -> "np.ndarray":
        """Compute complexity measure."""
        raise_error(
            msg="Concrete classes need to implement compute_complexity().",
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
        return "vector"

    def compute(
        self,
        input: Dict[str, Any],
        extra_input: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
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

           * ``data`` : ROI-wise complexity measures as ``numpy.ndarray``
           * ``col_names`` : ROI labels for the complexity measures as list

        """
        # Initialize a ParcelAggregation
        parcel_aggregation = ParcelAggregation(
            parcellation=self.parcellation,
            method=self.agg_method,
            method_params=self.agg_method_params,
            masks=self.masks,
            on="BOLD",
        )
        # Extract the 2D time series using parcel aggregation
        parcel_aggregation_map = parcel_aggregation.compute(
            input=input, extra_input=extra_input
        )

        # Compute complexity measure
        parcel_aggregation_map["data"] = self.compute_complexity(
            parcel_aggregation_map["data"]
        )

        return parcel_aggregation_map
