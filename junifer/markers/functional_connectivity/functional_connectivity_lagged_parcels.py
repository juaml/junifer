"""Provide class for lagged functional connectivity using parcels."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL


from typing import Any, Optional, Union

from ...api.decorators import register_marker
from ..parcel_aggregation import ParcelAggregation
from .functional_connectivity_lagged_base import (
    FunctionalConnectivityLaggedBase,
)


__all__ = ["FunctionalConnectivityLaggedParcels"]


@register_marker
class FunctionalConnectivityLaggedParcels(FunctionalConnectivityLaggedBase):
    """Class for lagged functional connectivity using parcellations.

    Parameters
    ----------
    parcellation : str or list of str
        The name(s) of the parcellation(s) to use.
        See :func:`.list_data` for options.
    max_lag : int
        The time lag range. The lag ranges from ``-max_lag`` to ``+max_lag``
        time points.
    agg_method : str, optional
        The method to perform aggregation using.
        See :func:`.get_aggfunc_by_name` for options
        (default "mean").
    agg_method_params : dict, optional
        Parameters to pass to the aggregation function.
        See :func:`.get_aggfunc_by_name` for options
        (default None).
    masks : str, dict or list of dict or str, optional
        The specification of the masks to apply to regions before extracting
        signals. Check :ref:`Using Masks <using_masks>` for more details.
        If None, will not apply any mask (default None).
    name : str, optional
        The name of the marker. If None, will use
        ``BOLD_FunctionalConnectivityLaggedParcels`` (default None).

    """

    def __init__(
        self,
        parcellation: Union[str, list[str]],
        max_lag: int,
        agg_method: str = "mean",
        agg_method_params: Optional[dict] = None,
        masks: Union[str, dict, list[Union[dict, str]], None] = None,
        name: Optional[str] = None,
    ) -> None:
        self.parcellation = parcellation
        super().__init__(
            max_lag=max_lag,
            agg_method=agg_method,
            agg_method_params=agg_method_params,
            masks=masks,
            name=name,
        )

    def aggregate(
        self, input: dict[str, Any], extra_input: Optional[dict] = None
    ) -> dict:
        """Perform parcel aggregation.

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
        return ParcelAggregation(
            parcellation=self.parcellation,
            method=self.agg_method,
            method_params=self.agg_method_params,
            masks=self.masks,
            on="BOLD",
        ).compute(input=input, extra_input=extra_input)
