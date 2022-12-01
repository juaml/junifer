"""Provide class for regional homogeneity (ReHo) on parcels."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL


from typing import Any, Dict, Optional

from ...api.decorators import register_marker
from ...utils import logger
from ..parcel_aggregation import ParcelAggregation
from .reho_base import ReHoBase


@register_marker
class ReHoParcels(ReHoBase):
    """Class for regional homogeneity on parcels.

    Parameters
    ----------
    parcellation : str
        The name of the parcellation. Check valid options by calling
        :func:`junifer.data.parcellations.list_parcellations`.
    reho_params : dict, optional
        Extra parameters for computing ReHo map as a dictionary (default None).
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

    def __init__(
        self,
        parcellation: str,
        reho_params: Optional[Dict] = None,
        agg_method: str = "mean",
        agg_method_params: Optional[Dict] = None,
        mask: Optional[str] = None,
        name: Optional[str] = None,
    ) -> None:
        self.parcellation = parcellation
        self.reho_params = reho_params
        self.agg_method = agg_method
        self.agg_method_params = agg_method_params
        self.mask = mask
        super().__init__(name=name)

    def compute(
        self,
        input: Dict[str, Any],
        extra_input: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Compute.

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

            * ``data`` : the actual computed values as a 1D numpy.ndarray
            * ``columns`` : the column labels for the parcels as a list
            * ``row_names`` : ``None``

        """
        logger.info("Calculating ReHO for parcels.")
        # Calculate reho map
        if self.reho_params is not None:
            reho_map = self.compute_reho_map(input=input, **self.reho_params)
        else:
            reho_map = self.compute_reho_map(input=input)
        # Initialize parcel aggregation
        parcel_aggregation = ParcelAggregation(
            parcellation=self.parcellation,
            method=self.agg_method,
            method_params=self.agg_method_params,
            mask=self.mask,
            on="BOLD",
        )
        # Perform aggregation on reho map
        parcel_aggregation_input = {"data": reho_map}
        output = parcel_aggregation.compute(input=parcel_aggregation_input)
        # # Expand row dimension
        # output["data"] = output["data"][np.newaxis, :]
        # # Delete row_names
        # del output["row_names"]
        # # Set row_cols_name to None
        # output["rows_col_name"] = None
        return output
