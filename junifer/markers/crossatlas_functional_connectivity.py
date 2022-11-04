"""Provide marker class to calculate cross-atlas FC."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
#          Kaustubh R. Patil <k.patil@fz-juelich.de>
# License: AGPL

from typing import Any, Dict, List, Optional

import pandas as pd

from ..api.decorators import register_marker
from ..storage import BaseFeatureStorage
from ..utils import logger
from .base import BaseMarker
from .parcel_aggregation import ParcelAggregation
from .utils import _correlate_dataframes


@register_marker
class CrossAtlasFC(BaseMarker):
    """Class for calculating parcel-wise correlations between two atlases.

    Parameters
    ----------
    atlas_one : str
        The name of the first atlas.
    atlas_two : str
        The name of the second atlas.
    aggregation_method : str, optional
        The aggregation method (default "mean").
    correlation_method : str, optional
        Any method that can be passed to
        :func:`pandas.DataFrame.corr` (default "pearson").
    name : str, optional
        The name of the marker. If None, will use the class name
        (default None).
    """

    def __init__(
        self,
        atlas_one: str,
        atlas_two: str,
        aggregation_method: str = "mean",
        correlation_method: str = "pearson",
        name: str = None,
    ) -> None:
        self.atlas_one = atlas_one
        self.atlas_two = atlas_two
        self.aggregation_method = aggregation_method
        self.correlation_method = correlation_method
        super().__init__(on=["BOLD"], name=name)

    def get_valid_inputs(self) -> List[str]:
        """Get valid data types for input.

        Returns
        -------
        list of str
            The list of data types that can be used as input for this marker

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
        kind,
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
        logger.debug(f"Storing BOLD-based marker in {storage}")
        storage.store(kind="matrix", **out)

    def compute(
        self,
        input: Dict[str, Any],
        extra_input: Optional[Dict] = None,
    ) -> Dict:
        """Compute.

        Take a timeseries, parcellate them with two different parcellation
        schemes, and get parcel-wise correlations between the two different
        parcellated time series. Shape of output matrix corresponds to number
        of ROIs in (atlas_two, atlas_one).

        Parameters
        ----------
        input : dict
            The BOLD data as a dictionary.
        extra_input : dict, optional
            The other fields in the pipeline data object (default None).

        Returns
        -------
        dict
            The computed result as dictionary. This will be either returned
            to the user or stored in the storage by calling the store method
            with this as a parameter. The dictionary has the following keys:

            * data : the correlation values between the two parcellations as
            a numpy.ndarray
            * col_names : the ROIs for first parcellation as a list
            * row_names : the ROIs for second parcellation as a list

        """
        logger.debug(
            "Aggregating time series in"
            f" {self.atlas_one} and {self.atlas_two} atlases."
        )
        # Initialize a ParcelAggregation
        atlas_one_dict = ParcelAggregation(
            atlas=self.atlas_one,
            method=self.aggregation_method,
        ).compute(input)
        atlas_two_dict = ParcelAggregation(
            atlas=self.atlas_two,
            method=self.aggregation_method,
        ).compute(input)

        parcellated_ts_one = atlas_one_dict["data"]
        parcellated_ts_two = atlas_two_dict["data"]
        # columns should be named after parcellation 1
        # rows should be named after parcellation 2

        result = _correlate_dataframes(
            pd.DataFrame(parcellated_ts_one),
            pd.DataFrame(parcellated_ts_two),
            method=self.correlation_method,
        ).values

        return {
            "data": result,
            "col_names": atlas_one_dict["columns"],
            "row_names": atlas_two_dict["columns"],
        }
