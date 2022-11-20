"""Provide class for complexity features for a timeseries."""

# Authors: Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

import numpy as np

from ..api.decorators import register_marker
from ..utils import logger
from .base import BaseMarker
from .parcel_aggregation import ParcelAggregation
from .utils import _calculate_complexity

if TYPE_CHECKING:
    from junifer.storage import BaseFeatureStorage


@register_marker
class Complexity(BaseMarker):
    """Class for the extraction of complexity features from a timeseries.

    Parameters
    ----------
    parcellation : str
        The name of the parcellation. Check valid options by calling
        :func:`junifer.data.parcellations.list_parcellations`.
    aggregation_method : str, optional
        The method to perform aggregation using. Check valid options in
        :func:`junifer.stats.get_aggfunc_by_name` (default "mean").
    name : str, optional
        The name of the marker. If None, will use the class name (default
        None).

    """

    def __init__(
        self,
        parcellation: str,
        aggregation_method: str = "mean",
        feature_kinds: Optional[Union[str, List[str]]] = None,
        name: Optional[str] = None,
    ) -> None:
        self.parcellation = parcellation
        self.aggregation_method = aggregation_method
        # feature_kinds should be a dctionary with keys as the function names,
        # and values as another dictionary with function parameters.  
        if feature_kinds is None:
            self.feature_kinds = {
                '_range_entropy': {
                    'm': 2,
                    'tol': 0.5
                    },
                    '_range_entropy_auc': {
                    'm': 2,
                    'n_r': 100
                    },
                '_perm_entropy': {
                    'm': 4,
                    'tau': 1
                    },
                '_weighted_perm_entropy': {
                    'm': 4,
                    'tau': 1
                    }
                }
        elif isinstance(feature_kinds, str):
            self.feature_kinds = [feature_kinds]          

        super().__init__(name=name)

    def get_valid_inputs(self) -> List[str]:
        """Get valid data types for input.

        Returns
        -------
        list of str
            The list of data types that can be used as input for this marker.

        """
        return ["BOLD"]

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
        return ["matrix"]

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
        storage.store(kind="matrix", **out)

    def compute(
        self,
        input: Dict[str, Any],
        extra_input: Optional[Dict] = None,
    ) -> Dict:
        """Compute.

        Change: Take a timeseries of brain areas, and calculate several
        measures of complexity ROI-wise.

        Parameters
        ----------
        input : dict
            The BOLD data as dictionary.
        extra_input : dict, optional
            The other fields in the pipeline data object (default None).

        Returns
        -------
        dict
            The computed result as dictionary. The following data will be
            included in the dictionary:
            * ``data`` : complexity features matrix as a numpy.ndarray.
            * ``row_names`` : row names as a list
            * ``col_names`` : column names as a list

        References
        ----------
        .. [1] A. Omidvarnia et al. (2018)
               Range Entropy: A Bridge between Signal Complexity and
               Self-Similarity, Entropy, vol. 20, no. 12, p. 962, 2018.

        """
        logger.debug("Calculating root sum of squares of edgewise timeseries.")
        # Initialize a ParcelAggregation
        parcel_aggregation = ParcelAggregation(
            parcellation=self.parcellation,
            method=self.aggregation_method,
        )
        # Compute the parcel aggregation
        out = parcel_aggregation.compute(input=input, extra_input=extra_input)

        # Calculate complexity
        out["data"] = _calculate_complexity(out["data"], self.feature_kinds)

        # Set correct column label
        out["columns"] = ["complexity"]
        return out
        