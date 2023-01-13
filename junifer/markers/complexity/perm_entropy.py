"""Provide class for permutation entropy of a time series."""

# Authors: Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL

from typing import Dict, List, Optional, Union

from ...api.decorators import register_marker
from ...utils import logger
from ..utils import _perm_entropy
from .complexity_base import ComplexityBase


@register_marker
class PermEntropy(ComplexityBase):
    """Class for permutation entropy of a time series.

    Parameters
    ----------
    parcellation : str or list of str
        The name(s) of the parcellation(s). Check valid options by calling
        :func:`junifer.data.parcellations.list_parcellations`.
    agg_method : str, optional
        The method to perform aggregation using. Check valid options in
        :func:`junifer.stats.get_aggfunc_by_name` (default "mean").
    agg_method_params : dict, optional
        Parameters to pass to the aggregation function. Check valid options in
        :func:`junifer.stats.get_aggfunc_by_name` (default None).
    mask : str, optional
        The name of the mask to apply to regions before extracting signals.
        Check valid options by calling :func:`junifer.data.masks.list_masks`
        (default None).
    perm_entropy_params : dict, optional
        Parameters to pass to the permutation entropy calculation function. 
        For more information, check out :
        func:`junfier.markers.utils._perm_entropy`.
        If None, value is set to
        {"m": 2, "delay": 1} (default None).
    name : str, optional
        The name of the marker. If None, it will use the class name
        (default None).

    """

    def __init__(
        self,
        parcellation: Union[str, List[str]],
        agg_method: str = "mean",
        agg_method_params: Optional[Dict] = None,
        mask: Optional[str] = None,
        perm_entropy_params: Optional[Dict] = None,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(
            parcellation=parcellation,
            agg_method=agg_method,
            agg_method_params=agg_method_params,
            mask=mask,
            name=name,
        )
        if perm_entropy_params is None:
            self.perm_entropy_params = {"m": 2, "delay": 1}
        else:
            self.perm_entropy_params = perm_entropy_params

    def compute(self, input: Dict, extra_input: Optional[Dict] = None) -> Dict:
        """Compute.

        Take a timeseries of brain areas, and calculate the permutation entropy[1].

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

            * ``data`` : computed data as a numpy.ndarray.
            * ``row_names`` : row names as a list
            * ``col_names`` : column names as a list
            * ``matrix_kind`` : the kind of matrix (tril, triu or full)

        References
        ----------
        .. [1] A. Omidvarnia et al. (2018)
           Range Entropy: A Bridge between Signal Complexity and
           Self-Similarity, Entropy, vol. 20, no. 12, p. 962, 2018.

        """
        # Extract aggregated BOLD timeseries
        bold_timeseries = self._extract_bold_timeseries(input=input)

        # Calculate permutation entropy
        logger.info("Calculating permutation entropy.")
        roi_wise_perm_entropy_map = _perm_entropy(
            bold_timeseries["data"], self.perm_entropy_params
        )  # n_roi X 1
        # Initialize output
        output = {}
        output["data"] = roi_wise_perm_entropy_map
        output["col_names"] = "perm_entropy"
        output["row_names"] = bold_timeseries["columns"]
        return output
