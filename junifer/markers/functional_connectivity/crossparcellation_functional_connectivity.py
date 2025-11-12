"""Provide marker class to calculate cross-parcellation FC."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
#          Kaustubh R. Patil <k.patil@fz-juelich.de>
# License: AGPL

from typing import Any, ClassVar, Optional, Union

import pandas as pd

from ...api.decorators import register_marker
from ...typing import Dependencies, MarkerInOutMappings
from ...utils import logger, raise_error
from ..base import BaseMarker
from ..parcel_aggregation import ParcelAggregation
from ..utils import _correlate_dataframes


__all__ = ["CrossParcellationFC"]


@register_marker
class CrossParcellationFC(BaseMarker):
    """Class for calculating parcel-wise correlations with 2 parcellations.

    Parameters
    ----------
    parcellation_one : str
        The name of the first parcellation.
    parcellation_two : str
        The name of the second parcellation.
    agg_method : str, optional
        The method to perform aggregation using.
        See :func:`.get_aggfunc_by_name` for options
        (default "mean").
    agg_method_params : dict, optional
        Parameters to pass to the aggregation function.
        See :func:`.get_aggfunc_by_name` for options
        (default None).
    corr_method : str, optional
        Any method that can be passed to
        :meth:`pandas.DataFrame.corr` (default "pearson").
    masks : str, dict or list of dict or str, optional
        The specification of the masks to apply to regions before extracting
        signals. Check :ref:`Using Masks <using_masks>` for more details.
        If None, will not apply any mask (default None).
    name : str, optional
        The name of the marker. If None, will use
        ``BOLD_CrossParcellationFC`` (default None).

    """

    _DEPENDENCIES: ClassVar[Dependencies] = {"nilearn"}

    _MARKER_INOUT_MAPPINGS: ClassVar[MarkerInOutMappings] = {
        "BOLD": {
            "functional_connectivity": "matrix",
        },
    }

    def __init__(
        self,
        parcellation_one: str,
        parcellation_two: str,
        agg_method: str = "mean",
        agg_method_params: Optional[dict] = None,
        corr_method: str = "pearson",
        masks: Union[str, dict, list[Union[dict, str]], None] = None,
        name: Optional[str] = None,
    ) -> None:
        if parcellation_one == parcellation_two:
            raise_error(
                "The two parcellations must be different.",
            )
        self.parcellation_one = parcellation_one
        self.parcellation_two = parcellation_two
        self.agg_method = agg_method
        self.agg_method_params = agg_method_params
        self.corr_method = corr_method
        self.masks = masks
        super().__init__(on=["BOLD"], name=name)

    def compute(
        self,
        input: dict[str, Any],
        extra_input: Optional[dict] = None,
    ) -> dict:
        """Compute.

        Take a timeseries, parcellate them with two different parcellation
        schemes, and get parcel-wise correlations between the two different
        parcellated time series. Shape of output matrix corresponds to number
        of ROIs in (parcellation_two, parcellation_one).

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

            * ``functional_connectivity`` : dictionary with the following keys:

              - ``data`` : correlation between the two parcellations as
                           ``numpy.ndarray``
              - ``col_names`` : ROI labels for first parcellation as list of
                                str
              - ``row_names`` : ROI labels for second parcellation as list of
                                str

        """
        logger.debug(
            "Aggregating time series in"
            f" {self.parcellation_one} and "
            f"{self.parcellation_two} parcellations."
        )
        # Perform aggregation using two parcellations
        aggregation_parcellation_one = ParcelAggregation(
            parcellation=self.parcellation_one,
            method=self.agg_method,
            method_params=self.agg_method_params,
            masks=self.masks,
            on="BOLD",
        ).compute(input, extra_input=extra_input)
        aggregation_parcellation_two = ParcelAggregation(
            parcellation=self.parcellation_two,
            method=self.agg_method,
            method_params=self.agg_method_params,
            masks=self.masks,
            on="BOLD",
        ).compute(input, extra_input=extra_input)

        return {
            "functional_connectivity": {
                "data": _correlate_dataframes(
                    pd.DataFrame(
                        aggregation_parcellation_one["aggregation"]["data"]
                    ),
                    pd.DataFrame(
                        aggregation_parcellation_two["aggregation"]["data"]
                    ),
                    method=self.corr_method,
                ).values,
                # Columns should be named after parcellation 1
                "col_names": aggregation_parcellation_one["aggregation"][
                    "col_names"
                ],
                # Rows should be named after parcellation 2
                "row_names": aggregation_parcellation_two["aggregation"][
                    "col_names"
                ],
            },
        }
