"""Provide class for weighted permutation entropy of a time series."""

# Authors: Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL

from typing import Dict, List, Optional, Union

from ...api.decorators import register_marker
from ...utils import logger
from ..parcel_aggregation import ParcelAggregation
from ..utils import _weighted_perm_entropy
from .complexity_base import ComplexityBase


@register_marker
class WeightedPermEntropy(ComplexityBase):
    """Class for weighted permutation entropy of a time series.

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
    params : dict, optional
        Parameters to pass to the weighted permutation entropy calculation
        function.
        For more information, check out
        ``junifer.markers.utils._weighted_perm_entropy``. If None, value
        is set to {"m": 2, "delay": 1} (default None).
    name : str, optional
        The name of the marker. If None, it will use the class name
        (default None).

    """

    def __init__(
        self,
        parcellation: Union[str, List[str]],
        agg_method: str = "mean",
        agg_method_params: Optional[Dict] = None,
        mask: Union[str, Dict, None] = None,
        params: Optional[Dict] = None,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(
            parcellation=parcellation,
            agg_method=agg_method,
            agg_method_params=agg_method_params,
            mask=mask,
            name=name,
        )
        if params is None:
            self.params = {"m": 4, "delay": 1}
        else:
            self.params = params

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
        return "matrix"

    def compute(self, input: Dict, extra_input: Optional[Dict] = None) -> Dict:
        """Compute.

        Take a timeseries of brain areas, and calculate the weighted
        permutation entropy [1].

        Parameters
        ----------
        input : dict
            The BOLD data as dictionary.
        extra_input : dict, optional
            The other fields in the pipeline data object (default None).

        Returns
        -------
        dict
            The computed result as dictionary. The dictionary has the following
            keys:

            * ``data`` : computed data as a numpy.ndarray.
            * ``row_names`` : row names as a list
            * ``col_names`` : column names as a list
            * ``matrix_kind`` : the kind of matrix (tril, triu or full)

        References
        ----------
        .. [1] Fadlallah, B., Chen, B., Keil, A., & Principe, J. (2013)
               Weighted-permutation entropy: A complexity measure for
               time series incorporating amplitude information.
               Physical Review E, 87(2), 022911.

        """
        # Extract aggregated BOLD timeseries
        logger.info("Calculating weighted permutation entropy.")

        # Calculate range entropy
        parcel_aggregation = ParcelAggregation(
            parcellation=self.parcellation,
            method=self.agg_method,
            method_params=self.agg_method_params,
            mask=self.mask,
        )
        # Compute the parcel aggregation
        output = parcel_aggregation.compute(
            input=input, extra_input=extra_input
        )
        feature_map = _weighted_perm_entropy(
            output["data"], self.params
        )  # 1 X n_roi

        # Initialize output
        out = output.copy()
        out["data"] = feature_map
        out["col_names"] = output["columns"]
        del out["columns"]

        return out
