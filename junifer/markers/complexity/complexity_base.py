"""Provide base class for complexity."""

# Authors: Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
# License: AGPL

from typing import Any, Dict, List, Optional, Union

from ..base import BaseMarker
from ..parcel_aggregation import ParcelAggregation


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
    mask : str, optional
        The name of the mask to apply to regions before extracting signals.
        Check valid options by calling :func:`junifer.data.masks.list_masks`
        (default None).
    name : str, optional
        The name of the marker. If None, it will use the class name
        (default None).

    """

    _DEPENDENCIES = {"nilearn", "neurokit2"}

    def __init__(
        self,
        parcellation: Union[str, List[str]],
        agg_method: str = "mean",
        agg_method_params: Optional[Dict] = None,
        mask: Optional[str] = None,
        name: Optional[str] = None,
    ) -> None:
        self.parcellation = parcellation
        self.agg_method = agg_method
        self.agg_method_params = agg_method_params
        self.mask = mask
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

    def _extract_bold_timeseries(self, input: Dict[str, Any]) -> Dict:
        """Extract BOLD time series.

        Parameters
        ----------
        input : dict
            The BOLD data as dictionary.

        Returns
        -------
        numpy.ndarray
            The extracted BOLD time series.

        """
        # Initialize a ParcelAggregation
        parcel_aggregation = ParcelAggregation(
            parcellation=self.parcellation,
            method=self.agg_method,
            method_params=self.agg_method_params,
            mask=self.mask,
            on="BOLD",
        )
        # Extract the 2D time series using parcel aggregation
        parcel_aggregation_output = parcel_aggregation.compute(input=input)
        return parcel_aggregation_output
