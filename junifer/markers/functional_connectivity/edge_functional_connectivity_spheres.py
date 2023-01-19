"""Provide class for edge-centric functional connectivity using spheres."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Any, Dict, Optional

from ...api.decorators import register_marker
from ..sphere_aggregation import SphereAggregation
from ..utils import _ets, raise_error
from .functional_connectivity_base import FunctionalConnectivityBase


@register_marker
class EdgeCentricFCSpheres(FunctionalConnectivityBase):
    """Class for edge-centric FC using coordinates (spheres).

    Parameters
    ----------
    coords : str
        The name of the coordinates list to use. See
        :func:`junifer.data.coordinates.list_coordinates` for options.
    radius : float, optional
        The radius of the sphere in mm. If None, the signal will be extracted
        from a single voxel. See :class:`nilearn.maskers.NiftiSpheresMasker`
        for more information (default None).
    agg_method : str, optional
        The aggregation method to use.
        See :func:`junifer.stats.get_aggfunc_by_name` for more information
        (default None).
    agg_method_params : dict, optional
        The parameters to pass to the aggregation method (default None).
    cor_method : str, optional
        The method to perform correlation using. Check valid options in
        :class:`nilearn.connectome.ConnectivityMeasure` (default "covariance").
    cor_method_params : dict, optional
        Parameters to pass to the correlation function. Check valid options in
        :class:`nilearn.connectome.ConnectivityMeasure` (default None).
    mask : str, optional
        The name of the mask to apply to regions before extracting signals.
        Check valid options by calling :func:`junifer.data.masks.list_masks`
        (default None).
    name : str, optional
        The name of the marker. By default, it will use
        KIND_EdgeCentricFCSpheres where KIND is the kind of data it
        was applied to (default None).

    References
    ----------
    .. [1] Jo et al. (2021)
            Subject identification using
            edge-centric functional connectivity
            doi: https://doi.org/10.1016/j.neuroimage.2021.118204

    """

    def __init__(
        self,
        coords: str,
        radius: Optional[float] = None,
        agg_method: str = "mean",
        agg_method_params: Optional[Dict] = None,
        cor_method: str = "covariance",
        cor_method_params: Optional[Dict] = None,
        mask: Optional[str] = None,
        name: Optional[str] = None,
    ) -> None:
        self.coords = coords
        self.radius = radius
        if radius is None or radius <= 0:
            raise_error(f"radius should be > 0: provided {radius}")
        super().__init__(
            agg_method=agg_method,
            agg_method_params=agg_method_params,
            cor_method=cor_method,
            cor_method_params=cor_method_params,
            mask=mask,
            name=name,
        )

    def aggregate(self, input: Dict[str, Any]) -> Dict:
        """Perform sphere aggregation."""
        sphere_aggregation = SphereAggregation(
            coords=self.coords,
            radius=self.radius,
            method=self.agg_method,
            method_params=self.agg_method_params,
            mask=self.mask,
            on="BOLD",
        )
        bold_aggregated = sphere_aggregation.compute(input)
        ets, edge_names = _ets(
            bold_aggregated["data"], bold_aggregated["columns"]
        )

        return dict(data=ets, columns=edge_names)
