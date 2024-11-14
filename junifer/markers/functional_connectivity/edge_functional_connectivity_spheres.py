"""Provide class for edge-centric functional connectivity using spheres."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Any, Optional, Union

from ...api.decorators import register_marker
from ..sphere_aggregation import SphereAggregation
from ..utils import _ets, raise_error
from .functional_connectivity_base import FunctionalConnectivityBase


__all__ = ["EdgeCentricFCSpheres"]


@register_marker
class EdgeCentricFCSpheres(FunctionalConnectivityBase):
    """Class for edge-centric FC using coordinates (spheres).

    Parameters
    ----------
    coords : str
        The name of the coordinates list to use.
        See :func:`.list_data` for options.
    radius : positive float, optional
        The radius of the sphere around each coordinates in millimetres.
        If None, the signal will be extracted from a single voxel.
        See :class:`.JuniferNiftiSpheresMasker` for more information
        (default None).
    allow_overlap : bool, optional
        Whether to allow overlapping spheres. If False, an error is raised if
        the spheres overlap (default False).
    agg_method : str, optional
        The method to perform aggregation using.
        See :func:`.get_aggfunc_by_name` for options
        (default "mean").
    agg_method_params : dict, optional
        Parameters to pass to the aggregation function.
        See :func:`.get_aggfunc_by_name` for options
        (default None).
    conn_method : str, optional
        The method to perform connectivity measure using.
        See :class:`.JuniferConnectivityMeasure` for options
        (default "correlation").
    conn_method_params : dict, optional
        Parameters to pass to :class:`.JuniferConnectivityMeasure`.
        If None, ``{"empirical": True}`` will be used, which would mean
        :class:`sklearn.covariance.EmpiricalCovariance` is used to compute
        covariance. If usage of :class:`sklearn.covariance.LedoitWolf` is
        desired, ``{"empirical": False}`` should be passed
        (default None).
    masks : str, dict or list of dict or str, optional
        The specification of the masks to apply to regions before extracting
        signals. Check :ref:`Using Masks <using_masks>` for more details.
        If None, will not apply any mask (default None).
    name : str, optional
        The name of the marker. If None, will use
        ``BOLD_EdgeCentricFCSpheres`` (default None).

    References
    ----------
    .. [1] Jo et al. (2021)
           Subject identification using edge-centric functional connectivity.
           https://doi.org/10.1016/j.neuroimage.2021.118204

    """

    def __init__(
        self,
        coords: str,
        radius: Optional[float] = None,
        allow_overlap: bool = False,
        agg_method: str = "mean",
        agg_method_params: Optional[dict] = None,
        conn_method: str = "correlation",
        conn_method_params: Optional[dict] = None,
        masks: Union[str, dict, list[Union[dict, str]], None] = None,
        name: Optional[str] = None,
    ) -> None:
        self.coords = coords
        self.radius = radius
        self.allow_overlap = allow_overlap
        if radius is None or radius <= 0:
            raise_error(f"radius should be > 0: provided {radius}")
        super().__init__(
            agg_method=agg_method,
            agg_method_params=agg_method_params,
            conn_method=conn_method,
            conn_method_params=conn_method_params,
            masks=masks,
            name=name,
        )

    def aggregate(
        self, input: dict[str, Any], extra_input: Optional[dict] = None
    ) -> dict:
        """Perform sphere aggregation and ETS computation.

        Parameters
        ----------
        input : dict
            A single input from the pipeline data object in which to compute
            the marker.
        extra_input : dict, optional
            The other fields in the pipeline data object. Useful for accessing
            other data kind that needs to be used in the computation. For
            example, the functional connectivity markers can make use of the
            confounds if available (default None).

        Returns
        -------
        dict
            The computed result as dictionary. This will be either returned
            to the user or stored in the storage by calling the store method
            with this as a parameter. The dictionary has the following keys:

            * ``aggregation`` : dictionary with the following keys:

                - ``data`` : ROI values as ``numpy.ndarray``
                - ``col_names`` : ROI labels as list of str

        """
        # Perform aggregation
        aggregation = SphereAggregation(
            coords=self.coords,
            radius=self.radius,
            allow_overlap=self.allow_overlap,
            method=self.agg_method,
            method_params=self.agg_method_params,
            masks=self.masks,
            on="BOLD",
        ).compute(input, extra_input=extra_input)
        # Compute edgewise timeseries
        ets, edge_names = _ets(
            bold_ts=aggregation["aggregation"]["data"],
            roi_names=aggregation["aggregation"]["col_names"],
        )

        return {
            "aggregation": {"data": ets, "col_names": edge_names},
        }
