"""Provide class for edge-centric functional connectivity using parcels."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Any, Dict, List, Optional, Union

from ...api.decorators import register_marker
from ..parcel_aggregation import ParcelAggregation
from ..utils import _ets
from .functional_connectivity_base import FunctionalConnectivityBase


@register_marker
class EdgeCentricFCParcels(FunctionalConnectivityBase):
    """Class for edge-centric FC using parcellations.

    Parameters
    ----------
    parcellation : str or list of str
        The name(s) of the parcellation(s). Check valid options by calling
        :func:`junifer.data.parcellations.list_parcellations`.
    agg_method : str, optional
        The method to perform aggregation of BOLD time series.
        Check valid options in :func:`junifer.stats.get_aggfunc_by_name`
        (default "mean").
    agg_method_params : dict, optional
        Parameters to pass to the aggregation function. Check valid options in
        :func:`junifer.stats.get_aggfunc_by_name` (default None).
    cor_method : str, optional
        The method to perform correlation. Check valid options in
        :class:`nilearn.connectome.ConnectivityMeasure`
        (default "covariance").
    cor_method_params : dict, optional
        Parameters to pass to the correlation function. Check valid options in
        :class:`nilearn.connectome.ConnectivityMeasure` (default None).
    mask : str, optional
        The name of the mask to apply to regions before extracting signals.
        Check valid options by calling :func:`junifer.data.masks.list_masks`
        (default None).
    name : str, optional
        The name of the marker. If None, will use the class name (default
        None).

    References
    ----------
    .. [1] Jo et al. (2021)
            Subject identification using
            edge-centric functional connectivity
            doi: https://doi.org/10.1016/j.neuroimage.2021.118204

    """

    def __init__(
        self,
        parcellation: Union[str, List[str]],
        agg_method: str = "mean",
        agg_method_params: Optional[Dict] = None,
        cor_method: str = "covariance",
        cor_method_params: Optional[Dict] = None,
        mask: Optional[str] = None,
        name: Optional[str] = None,
    ) -> None:
        self.parcellation = parcellation
        super().__init__(
            agg_method=agg_method,
            agg_method_params=agg_method_params,
            cor_method=cor_method,
            cor_method_params=cor_method_params,
            mask=mask,
            name=name,
        )

    def aggregate(self, input: Dict[str, Any]) -> Dict:
        """Perform parcel aggregation."""
        parcel_aggregation = ParcelAggregation(
            parcellation=self.parcellation,
            method=self.agg_method,
            method_params=self.agg_method_params,
            mask=self.mask,
            on="BOLD",
        )

        bold_aggregated = parcel_aggregation.compute(input)
        ets, edge_names = _ets(
            bold_aggregated["data"], bold_aggregated["columns"]
        )

        return dict(data=ets, columns=edge_names)
