"""Provide class for temporal SNR using parcels."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL

from typing import Any, Dict, List, Optional, Union

from ...api.decorators import register_marker
from ..parcel_aggregation import ParcelAggregation
from .temporal_snr_base import TemporalSNRBase


@register_marker
class TemporalSNRParcels(TemporalSNRBase):
    """Class for temporal signal-to-noise ratio using parcellations.

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
        The name of the marker. If None, will use the class name (default
        None).

    """

    def __init__(
        self,
        parcellation: Union[str, List[str]],
        agg_method: str = "mean",
        agg_method_params: Optional[Dict] = None,
        masks: Union[str, Dict, List[Union[Dict, str]], None] = None,
        name: Optional[str] = None,
    ) -> None:
        self.parcellation = parcellation
        super().__init__(
            agg_method=agg_method,
            agg_method_params=agg_method_params,
            masks=masks,
            name=name,
        )

    def aggregate(self, input: Dict[str, Any]) -> Dict:
        """Perform parcel aggregation."""
        parcel_aggregation = ParcelAggregation(
            parcellation=self.parcellation,
            method=self.agg_method,
            method_params=self.agg_method_params,
            masks=self.masks,
            on="BOLD",
        )
        # Return the 2D timeseries after parcel aggregation
        return parcel_aggregation.compute(input)
