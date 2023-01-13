"""Provide class for sample entropy of a time series."""

# Authors: Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL

from typing import Dict, List, Optional, Union

from ...api.decorators import register_marker
from ...utils import logger
from ..utils import _sample_entropy
from .complexity_base import ComplexityBase


@register_marker
class SampleEntropy(ComplexityBase):
    """Class for sample entropy of a time series.

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
    params : dict, optional
        Parameters to pass to the sample entropy calculation function. 
        For more information, check out :
        func:`junfier.markers.utils._sample_entropy`.
        If None, value is set to
        {"m": 2, "delay": 1, "tol": 0.5} (default None).
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
        params: Optional[Dict] = None,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(
            parcellation=parcellation,
            agg_method=agg_method,
            agg_method_params=agg_method_params,
            mask=mask,
            name=name,
        )
        if params is None:
            self.params = {"m": 4, "delay": 1, "tol": 0.5}
        else:
            self.params = params

    def compute(self, input: Dict, extra_input: Optional[Dict] = None) -> Dict:
        """Compute.

        Take a timeseries of brain areas, and calculate the sample entropy [1].

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
        .. [1] Richman, J., Moorman, J.
            Physiological time-series analysis using approximate entropy and
            sample entropy, Am. J. Physiol. Heart Circ. Physiol.,
            278 (6) (2000), pp. H2039-2049

        See also
        ---------
        https://neuropsychology.github.io/NeuroKit/functions/complexity.html

        """
        # Extract aggregated BOLD timeseries
        bold_timeseries = self._extract_bold_timeseries(input=input)

        # Calculate sample entropy
        logger.info("Calculating sample entropy.")
        feature_map = _sample_entropy(
            bold_timeseries["data"], self.params
        )  # n_roi X 1
        # Initialize output
        output = {}
        output["data"] = feature_map
        output["col_names"] = "sample_entropy"
        output["row_names"] = bold_timeseries["columns"]
        return output
