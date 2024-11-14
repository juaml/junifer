"""Provide class for the AUC of range entropy of a time series."""

# Authors: Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL

from typing import Optional, Union

import neurokit2 as nk
import numpy as np

from ...api.decorators import register_marker
from ...utils import logger, warn_with_log
from .complexity_base import ComplexityBase


__all__ = ["RangeEntropyAUC"]


@register_marker
class RangeEntropyAUC(ComplexityBase):
    """Class for AUC of range entropy values of a time series over r = 0 to 1.

    Parameters
    ----------
    parcellation : str or list of str
        The name(s) of the parcellation(s) to use.
        See :func:`.list_data` for options.
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
        Parameters to pass to the range entropy calculation function. For more
        information, check out ``junifer.markers.utils._range_entropy``.
        If None, value is set to {"m": 2, "delay": 1, "n_r": 10}
        (default None).
    name : str, optional
        The name of the marker. If None, it will use the class name
        (default None).

    Warnings
    --------
    This class is not automatically imported by junifer and requires you to
    import it explicitly. You can do it programmatically by
    ``from junifer.markers.complexity import RangeEntropyAUC`` or in the YAML
    by ``with: junifer.markers.complexity``.

    """

    def __init__(
        self,
        parcellation: Union[str, list[str]],
        agg_method: str = "mean",
        agg_method_params: Optional[dict] = None,
        masks: Union[str, dict, list[Union[dict, str]], None] = None,
        params: Optional[dict] = None,
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
            self.params = {"m": 2, "delay": 1, "n_r": 10}
        else:
            self.params = params

    def compute_complexity(
        self,
        extracted_bold_values: np.ndarray,
    ) -> np.ndarray:
        """Compute complexity measure.

        Take a timeseries of brain areas, calculate range entropy according to
        the method outlined in [1] across the range of tolerance value r from 0
        to 1, and compute its area under the curve.

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
        .. [1] A. Omidvarnia et al. (2018)
               Range Entropy: A Bridge between Signal Complexity and
               Self-Similarity.
               Entropy, vol. 20, no. 12, p. 962, 2018.

        See Also
        --------
        neurokit2.entropy_range

        """
        logger.info("Calculating AUC of range entropy.")

        emb_dim = self.params["m"]
        delay = self.params["delay"]
        n_r = self.params["n_r"]

        assert isinstance(emb_dim, int), "Embedding dimension must be integer."
        assert isinstance(delay, int), "Delay must be integer."
        assert isinstance(n_r, int), "n_r must be an integer."

        r_span = np.arange(0, 1, 1 / n_r)  # Tolerance r span
        _, n_roi = extracted_bold_values.shape
        range_en_auc_roi = np.zeros((n_roi, 1))

        for idx_roi in range(n_roi):
            sig = extracted_bold_values[:, idx_roi]

            range_ent_vec = np.zeros(n_r)
            idx_r = 0
            for tolerance in r_span:
                range_en_auc_roi_tmp = nk.entropy_range(
                    sig,
                    dimension=emb_dim,
                    delay=delay,
                    tolerance=tolerance,
                    method="mSampEn",  # RangeEn B
                )

                range_ent_vec[idx_r] = range_en_auc_roi_tmp[0]
                idx_r = idx_r + 1

            range_en_auc_roi[idx_roi] = np.trapz(range_ent_vec)

        range_en_auc_roi = range_en_auc_roi / n_r

        if np.isnan(np.sum(range_en_auc_roi)):
            warn_with_log("There is NaN in the auc of range entropy values!")

        return range_en_auc_roi.T  # 1 X n_roi
