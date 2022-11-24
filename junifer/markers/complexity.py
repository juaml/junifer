"""Provide class for complexity features for a timeseries."""

# Authors: Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL

from typing import TYPE_CHECKING, Any, Dict, List, Optional

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
        measure_types: dict = None,
        aggregation_method: str = "mean",
        name: Optional[str] = None,
    ) -> None:
        self.parcellation = parcellation
        self.aggregation_method = aggregation_method
        # measure_types should be a dctionary with keys as the function names,
        # and values as another dictionary with function parameters.
        if measure_types is None:
            self.measure_types = {
                "_range_entropy": {"m": 2, "tol": 0.5},
                "_range_entropy_auc": {"m": 2, "n_r": 10},
                "_perm_entropy": {"m": 4, "tau": 1},
                "_weighted_perm_entropy": {"m": 4, "tau": 1},
                "_sample_entropy": {"m": 2, "tau": 1, "tol": 0.5},
                "_multiscale_entropy_auc": {"m": 2, "tol": 0.5, "scale": 10},
                "_hurst_exponent": {"reserved": None},
            }
        else:
            self.measure_types = measure_types

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
        region-wise measures of complexity including range entropy and its
        area under the curve [1], permutation entropy [2], weighted
        permutation entropy [3], sample entropy [4], multiscale entropy based
        on sample entropy [5], and Hurst exponent based on the detrended
        fluctuation analysis method [6].

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
        .. [1] A. Omidvarnia et al.
               Range Entropy: A Bridge between Signal Complexity and
               Self-Similarity, Entropy, vol. 20, no. 12, p. 962, 2018.

        .. [2] Bandt, C., & Pompe, B.
               Permutation entropy: a natural complexity measure for time
               series. Physical review letters, 88(17), 174102, 2002

        .. [3] Fadlallah, B., Chen, B., Keil, A., & Principe, J.
               Weighted-permutation entropy: A complexity measure for time
               series incorporating amplitude information.
               Physical Review E, 87(2), 022911., 2013.

        .. [4] Richman, J., Moorman, J.
               Physiological time-series analysis using approximate entropy
               and sample entropy, Am. J. Physiol. Heart Circ. Physiol.,
               278 (6), pp. H2039-2049, 2000.

        .. [5] Costa, M., Goldberger, A. L., & Peng, C. K.
               Multiscale entropy analysis of complex physiologic time series.
               Physical review letters, 89(6), 068102, 2002.

        .. [6] Peng, C.; Havlin, S.; Stanley, H.E.; Goldberger, A.L.
               Quantification of scaling exponents and crossover phenomena in
               nonstationary heartbeat time series.
               Chaos Interdiscip. J. Nonlinear Sci., 5, 82–87, 1995


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
        tmp = _calculate_complexity(bold_ts, self.measure_types)
        out = {}
        out["data"] = tmp
        out["col_names"] = self.measure_types.keys()
        out["row_names"] = pa_dict["columns"]

        return out
