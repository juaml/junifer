"""Provide class for functional connectivity using maps."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Any, Optional, Union

from ...api.decorators import register_marker
from ..maps_aggregation import MapsAggregation
from .functional_connectivity_base import FunctionalConnectivityBase


__all__ = ["FunctionalConnectivityMaps"]


@register_marker
class FunctionalConnectivityMaps(FunctionalConnectivityBase):
    """Class for functional connectivity using maps.

    Parameters
    ----------
    maps : str
        The name of the map(s) to use.
        See :func:`.list_data` for options.
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
        ``BOLD_FunctionalConnectivityMaps`` (default None).

    """

    def __init__(
        self,
        maps: str,
        conn_method: str = "correlation",
        conn_method_params: Optional[dict] = None,
        masks: Union[str, dict, list[Union[dict, str]], None] = None,
        name: Optional[str] = None,
    ) -> None:
        self.maps = maps
        super().__init__(
            conn_method=conn_method,
            conn_method_params=conn_method_params,
            masks=masks,
            name=name,
        )

    def aggregate(
        self, input: dict[str, Any], extra_input: Optional[dict] = None
    ) -> dict:
        """Perform maps aggregation.

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
        return MapsAggregation(
            maps=self.maps,
            masks=self.masks,
            on="BOLD",
        ).compute(input=input, extra_input=extra_input)
