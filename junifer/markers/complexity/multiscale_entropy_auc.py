"""Provide class for the AUC of multiscale entropy of a time series."""

# Authors: Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL

from typing import TYPE_CHECKING, Dict, List, Optional, Union

from ...api.decorators import register_marker
from ...utils import logger
from ..utils import _multiscale_entropy_auc
from .complexity_base import ComplexityBase


if TYPE_CHECKING:
    import numpy as np


@register_marker
class MultiscaleEntropyAUC(ComplexityBase):
    """Class for AUC of multiscale entropy of a time series.

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
    masks : str, dict or list of dict or str, optional
        The specification of the masks to apply to regions before extracting
        signals. Check :ref:`Using Masks <using_masks>` for more details.
        If None, will not apply any mask (default None).
    params : dict, optional
        Parameters to pass to the AUC of multiscale entropy calculation
        function. For more information, check out
        ``junifer.markers.utils._multiscale_entropy_auc``. If None, value
        is set to {"m": 2, "tol": 0.5, "scale": 10} (default None).
    name : str, optional
        The name of the marker. If None, it will use the class name
        (default None).

    """

    def __init__(
        self,
        parcellation: Union[str, List[str]],
        agg_method: str = "mean",
        agg_method_params: Optional[Dict] = None,
        masks: Union[str, Dict, List[Union[Dict, str]], None] = None,
        params: Optional[Dict] = None,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(
            parcellation=parcellation,
            agg_method=agg_method,
            agg_method_params=agg_method_params,
            masks=masks,
            name=name,
        )
        if params is None:
            self.params = {"m": 2, "tol": 0.5, "scale": 10}
        else:
            self.params = params

    def compute_complexity(
        self,
        extracted_bold_values: "np.ndarray",
    ) -> "np.ndarray":
        """Compute complexity measure.

        Take a timeseries of brain areas, and calculate the AUC of
        multiscale entropy [1].

        Parameters
        ----------
        extracted_bold_values : numpy.ndarray
            The BOLD values extracted via parcel aggregation.

        Returns
        -------
        numpy.ndarray
            The values after computing complexity measure.

        References
        ----------
        .. [1] Costa, M., Goldberger, A. L., & Peng, C. K.
               Multiscale entropy analysis of complex physiologic time series.
               Physical review letters, 89(6), 068102, 2002.

        """
        logger.info("Calculating AUC of multiscale entropy.")
        return _multiscale_entropy_auc(
            bold_ts=extracted_bold_values, params=self.params
        )  # 1 X n_roi
