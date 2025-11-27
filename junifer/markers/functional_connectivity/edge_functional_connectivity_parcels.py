"""Provide class for edge-centric functional connectivity using parcels."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Annotated, Any, Literal, Optional, Union

from pydantic import BeforeValidator

from ...api.decorators import register_marker
from ...datagrabber import DataType
from ..parcel_aggregation import ParcelAggregation
from ..utils import _ensure_list, _ets
from .functional_connectivity_base import FunctionalConnectivityBase


__all__ = ["EdgeCentricFCParcels"]


@register_marker
class EdgeCentricFCParcels(FunctionalConnectivityBase):
    """Class for edge-centric FC using parcellations.

    Parameters
    ----------
    parcellation : str or list of str
        The name(s) of the parcellation(s) to use.
        See :func:`.list_data` for options.
    agg_method : str, optional
        The aggregation function to use.
        See :func:`.get_aggfunc_by_name` for options
        (default "mean").
    agg_method_params : dict or None, optional
        The parameters to pass to the aggregation function.
        See :func:`.get_aggfunc_by_name` for options (default None).
    conn_method : str, optional
        The connectivity measure to use.
        See :class:`.JuniferConnectivityMeasure` for options
        (default "correlation").
    conn_method_params : dict or None, optional
        The parameters to pass to :class:`.JuniferConnectivityMeasure`.
        If None, ``{"empirical": True}`` will be used, which would mean
        :class:`sklearn.covariance.EmpiricalCovariance` is used to compute
        covariance. If usage of :class:`sklearn.covariance.LedoitWolf` is
        desired, ``{"empirical": False}`` should be passed
        (default None).
    masks : list of dict or str, or None, optional
        The specification of the masks to apply to regions before extracting
        signals. Check :ref:`Using Masks <using_masks>` for more details.
        If None, will not apply any mask (default None).
    name : str or None, optional
        The name of the marker.
        If None, will use the class name (default None).

    References
    ----------
    .. [1] Jo et al. (2021)
           Subject identification using edge-centric functional connectivity.
           https://doi.org/10.1016/j.neuroimage.2021.118204

    """

    parcellation: Annotated[
        Union[str, list[str]], BeforeValidator(_ensure_list)
    ]
    on: list[Literal[DataType.BOLD]] = [DataType.BOLD]  # noqa: RUF012

    def aggregate(
        self, input: dict[str, Any], extra_input: Optional[dict] = None
    ) -> dict:
        """Perform parcel aggregation and ETS computation.

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
        aggregation = ParcelAggregation(
            parcellation=self.parcellation,
            method=self.agg_method,
            method_params=self.agg_method_params,
            masks=self.masks,
            on=[DataType.BOLD],
        ).compute(input, extra_input=extra_input)
        # Compute edgewise timeseries
        ets, edge_names = _ets(
            bold_ts=aggregation["aggregation"]["data"],
            roi_names=aggregation["aggregation"]["col_names"],
        )

        return {
            "aggregation": {
                "data": ets,
                "col_names": edge_names,
            },
        }
