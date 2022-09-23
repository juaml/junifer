"""Provide marker class to calculate cross-atlas FC."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
#          Kaustubh R. Patil <k.patil@fz-juelich.de>
# License: AGPL

from typing import Dict, List, Optional

import pandas as pd

from ..api.decorators import register_marker
from ..utils import logger
from .base import BaseMarker
from .parcel import ParcelAggregation
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
    correlation_method : str or callable
        any method that can be passed to:
        https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.corr.html

    """

    def __init__(
        self,
        atlas_one: str,
        atlas_two: str,
        aggregation_method: str = "mean",
        correlation_method: str = "pearson",
        name: str = None,
    ) -> None:
        """Initialize the class."""
        self.atlas_one = atlas_one
        self.atlas_two = atlas_two
        self.aggregation_method = aggregation_method
        self.correlation_method = correlation_method
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
        return ["matrix"]

    def store(self, kind: str, out, storage) -> None:
        """Store.

        Parameters
        ----------
        kind
        out
        storage

        """
        logger.debug(f"Storing {kind} in {storage}")
        storage.store_matrix2d(**out)

    def compute(self, input: Dict, extra_input: Optional[Dict] = None) -> Dict:
        """Compute.

        Take a timeseries, parcellate them with two different parcellation
        schemes, and get parcel-wise correlations between the two different
        parcellated time series. Shape of output matrix corresponds to number
        of ROIs in (atlas_two, atlas_one).

        Parameters
        ----------
        input : dict of the BOLD data

        Returns
        -------
        dict
            The computed result as a dictionary.

        """

        logger.debug("Aggregating time series in both atlases.")
        # Initialize a ParcelAggregation
        final_out_dict = ParcelAggregation(
            atlas=self.atlas_one,
            method=self.aggregation_method,
        ).compute(input)
        atlas_two_dict = ParcelAggregation(
            atlas=self.atlas_two,
            method=self.aggregation_method,
        ).compute(input)

        parcellated_ts_one = final_out_dict["data"]
        parcellated_ts_two = atlas_two_dict["data"]
        # columns should be named after parcellation 1
        # rows should be named after parcellation 2
        final_out_dict["col_names"] = final_out_dict["columns"]
        del final_out_dict["columns"]
        final_out_dict["row_names"] = atlas_two_dict["columns"]

        final_out_dict["data"] = _correlate_dataframes(
            pd.DataFrame(parcellated_ts_one),
            pd.DataFrame(parcellated_ts_two),
            method=self.correlation_method,
        ).values
        return final_out_dict
