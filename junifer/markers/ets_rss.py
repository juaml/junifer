"""Provide class for root sum of squares of edgewise timeseries."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
#          Nicolás Nieto <n.nieto@fz-juelich.de>
#          Sami Hamdan <s.hamdan@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Annotated, Any, ClassVar, Literal, Optional, Union

import numpy as np
from pydantic import BeforeValidator

from ..api.decorators import register_marker
from ..datagrabber import DataType
from ..storage import StorageType
from ..typing import Dependencies, MarkerInOutMappings
from ..utils import logger
from .base import BaseMarker
from .parcel_aggregation import ParcelAggregation
from .utils import _ensure_list, _ets


__all__ = ["RSSETSMarker"]


@register_marker
class RSSETSMarker(BaseMarker):
    """Class for root sum of squares of edgewise timeseries.

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
    masks : list of dict or str, or None, optional
        The specification of the masks to apply to regions before extracting
        signals. Check :ref:`Using Masks <using_masks>` for more details.
        If None, will not apply any mask (default None).
    name : str or None, optional
        The name of the marker.
        If None, will use the class name (default None).

    """

    _DEPENDENCIES: ClassVar[Dependencies] = {"nilearn"}

    _MARKER_INOUT_MAPPINGS: ClassVar[MarkerInOutMappings] = {
        DataType.BOLD: {
            "rss_ets": StorageType.Timeseries,
        },
    }

    parcellation: Annotated[
        Union[str, list[str]], BeforeValidator(_ensure_list)
    ]
    agg_method: str = "mean"
    agg_method_params: Optional[dict] = None
    masks: Optional[list[Union[dict, str]]] = None
    on: list[Literal[DataType.BOLD]] = [DataType.BOLD]  # noqa: RUF012

    def compute(
        self,
        input: dict[str, Any],
        extra_input: Optional[dict] = None,
    ) -> dict:
        """Compute.

        Take a timeseries of brain areas, and calculate timeseries for each
        edge according to the method outlined in [1]_. For more information,
        check https://github.com/brain-networks/edge-ts/blob/master/main.m

        Parameters
        ----------
        input : dict
            The BOLD data as dictionary.
        extra_input : dict, optional
            The other fields in the pipeline data object (default None).

        Returns
        -------
        dict
            The computed result as dictionary. This will be either returned
            to the user or stored in the storage by calling the store method
            with this as a parameter. The dictionary has the following keys:

            * ``data`` : the actual computed values as a numpy.ndarray
            * ``col_names`` : the column labels for the computed values as list

        References
        ----------
        .. [1] Zamani Esfahlani et al. (2020)
               High-amplitude cofluctuations in cortical activity drive
               functional connectivity
               doi: 10.1073/pnas.2005531117

        """
        logger.debug("Calculating root sum of squares of edgewise timeseries.")
        # Perform aggregation
        aggregation = ParcelAggregation(
            parcellation=self.parcellation,
            method=self.agg_method,
            method_params=self.agg_method_params,
            on=[DataType.BOLD],
            masks=self.masks,
        ).compute(input=input, extra_input=extra_input)
        # Compute edgewise timeseries
        edge_ts, _ = _ets(aggregation["aggregation"]["data"])
        # Compute the RSS of edgewise timeseries
        rss = np.sum(edge_ts**2, 1) ** 0.5

        return {
            "rss_ets": {
                # Make it 2D
                "data": rss[:, np.newaxis],
                "col_names": ["root_sum_of_squares_ets"],
            }
        }
