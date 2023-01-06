"""Provide class for complexity features for a timeseries."""

# Authors: Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL

from typing import TYPE_CHECKING, Any, Dict, List, Optional

import numpy as np

# from ptpython.repl import embed
from ..api.decorators import register_marker
from ..utils import logger, warn_with_log
from .base import BaseMarker
from .parcel_aggregation import ParcelAggregation
from .utils import _hurst_exponent

if TYPE_CHECKING:
    from junifer.storage import BaseFeatureStorage


@register_marker
class HurstExponent(BaseMarker):
    """Class for the extraction of Hurst exponent from a timeseries.

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
        name: Optional[str] = None,
    ) -> None:
        self.parcellation = parcellation
        self.aggregation_method = aggregation_method
        # measure_type should be a dctionary with keys as the function names,
        # and values as another dictionary with function parameters.

        super().__init__(name=name)

    def get_valid_inputs(self) -> List[str]:
        """Get valid data types for input.

        Returns
        -------
        list of str
            The list of data types that can be used as input for this marker.

        """
        return ["BOLD"]

    def get_output_type(self, input: List[str]) -> List[str]:
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
        """Compute Hurst exponent.

        Change: Take a timeseries of brain areas, and calculate Hurst exponent
        based on the detrended fluctuation analysis method [1].

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
        .. [1] Peng, C.; Havlin, S.; Stanley, H.E.; Goldberger, A.L.
               Quantification of scaling exponents and crossover phenomena in
               nonstationary heartbeat time series.
               Chaos Interdiscip. J. Nonlinear Sci., 5, 82–87, 1995.

        """
        logger.debug("Calculating root sum of squares of edgewise timeseries.")
        # Initialize a ParcelAggregation
        parcel_aggregation = ParcelAggregation(
            parcellation=self.parcellation,
            method=self.aggregation_method,
        )
        # Compute the parcel aggregation dict
        pa_dict = parcel_aggregation.compute(
            input=input, extra_input=extra_input
        )

        # Calculate complexity and et correct column/row labels
        bold_ts = pa_dict["data"]
        params = {"method": "dfa"}
        tmp = _hurst_exponent(bold_ts, params)  # n_roi x 1
        method = params["method"]
        out = {}
        out["data"] = tmp
        out["col_names"] = f"HE_{method}"
        out["row_names"] = pa_dict["columns"]

        return out
