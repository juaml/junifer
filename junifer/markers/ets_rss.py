"""Provide class for root sum of squares of edgewise timeseries."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
#          Nicolás Nieto <n.nieto@fz-juelich.de>
#          Sami Hamdan <s.hamdan@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Any, ClassVar, Dict, List, Optional, Set, Union

import numpy as np

from ..api.decorators import register_marker
from ..utils import logger
from .base import BaseMarker
from .parcel_aggregation import ParcelAggregation
from .utils import _ets


@register_marker
class RSSETSMarker(BaseMarker):
    """Class for root sum of squares of edgewise timeseries.

    Parameters
    ----------
    parcellation : str or list of str
        The name(s) of the parcellation(s). Check valid options by calling
        :func:`.list_parcellations`.
    agg_method : str, optional
        The method to perform aggregation using. Check valid options in
        :func:`.get_aggfunc_by_name` (default "mean").
    agg_method_params : dict, optional
        Parameters to pass to the aggregation function. Check valid options in
        :func:`.get_aggfunc_by_name` (default None).
    masks : str, dict or list of dict or str, optional
        The specification of the masks to apply to regions before extracting
        signals. Check :ref:`Using Masks <using_masks>` for more details.
        If None, will not apply any mask (default None).
    name : str, optional
        The name of the marker. If None, will use the class name (default
        None).

    """

    _DEPENDENCIES: ClassVar[Set[str]] = {"nilearn"}

    def __init__(
        self,
        parcellation: Union[str, List[str]],
        agg_method: str = "mean",
        agg_method_params: Optional[Dict] = None,
        masks: Union[str, Dict, List[Union[Dict, str]], None] = None,
        name: Optional[str] = None,
    ) -> None:
        self.parcellation = parcellation
        self.agg_method = agg_method
        self.agg_method_params = agg_method_params
        self.masks = masks
        super().__init__(name=name)

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
        return "timeseries"

    def compute(
        self,
        input: Dict[str, Any],
        extra_input: Optional[Dict] = None,
    ) -> Dict:
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
            The computed result as dictionary. The dictionary has the following
            keys:

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
        # Initialize a ParcelAggregation
        parcel_aggregation = ParcelAggregation(
            parcellation=self.parcellation,
            method=self.agg_method,
            method_params=self.agg_method_params,
            masks=self.masks,
        )
        # Compute the parcel aggregation
        out = parcel_aggregation.compute(input=input, extra_input=extra_input)
        edge_ts, _ = _ets(out["data"])
        # Compute the RSS
        out["data"] = np.sum(edge_ts**2, 1) ** 0.5
        # Make it 2D
        out["data"] = out["data"][:, np.newaxis]
        # Set correct column label
        out["col_names"] = ["root_sum_of_squares_ets"]
        return out
