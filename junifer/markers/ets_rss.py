"""Provide class for root sum of squares of edgewise timeseries."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
#          Nicolás Nieto <n.nieto@fz-juelich.de>
#          Sami Hamdan <s.hamdan@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import TYPE_CHECKING, Any, Dict, List, Optional

import numpy as np

from ..api.decorators import register_marker
from ..utils import logger
from .base import BaseMarker
from .parcel import ParcelAggregation
from .utils import _ets


if TYPE_CHECKING:
    from junifer.storage import BaseFeatureStorage


@register_marker
class RSSETSMarker(BaseMarker):
    """Class for root sum of squares of edgewise timeseries.

    Parameters
    ----------
    atlas : str
        The name of the atlas. Check valid options by calling
        :func:`junifer.data.list_atlases`.
    aggregation_method : str, optional
        The aggregation method (default "mean").
    name : str, optional
        The name of the marker. If None, will use the class name (default
        None).

    """

    def __init__(
        self,
        atlas: str,
        aggregation_method: str = "mean",
        name: str = None,
    ) -> None:
        """Initialize the class."""
        self.atlas = atlas
        self.aggregation_method = aggregation_method
        super().__init__(on=["BOLD"], name=name)

    def get_output_kind(self, input: List[str]) -> List[str]:
        """Get output kind.

        Parameters
        ----------
        input : list of str
            The input to the marker. The list must contain the
            available Junifer Data dictionary keys.

        Returns
        -------
        list of str
            The updated list of output kinds, as storage possibilities.

        """
        return ["timeseries"]

    def store(
        self,
        kind: str,
        out: Dict[str, Any],
        storage: "BaseFeatureStorage",
    ) -> None:
        """Store.

        Parameters
        ----------
        kind : {"BOLD"}
            The data kind to store.
        out : dict
            The computed result as a dictionary to store.
        storage : storage-like
            The storage class, for example, SQLiteFeatureStorage.

        """
        logger.debug(f"Storing BOLD in {storage}")
        storage.store(kind="timeseries", **out)

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
            - data : the actual computed values as a numpy.ndarray
            - columns : the column labels for the computed values as a list
            - row_names (if more than one row is present in data): "scan"

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
            atlas=self.atlas,
            method=self.aggregation_method,
        )
        # Compute the parcel aggregation
        out = parcel_aggregation.compute(input=input, extra_input=extra_input)
        edge_ts = _ets(out["data"])
        # Compute the RSS
        out["data"] = np.sum(edge_ts**2, 1) ** 0.5
        # Set correct column label
        out["columns"] = ["root_sum_of_squares_ets"]
        return out
