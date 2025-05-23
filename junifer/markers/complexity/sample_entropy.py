"""Provide class for sample entropy of a time series."""

# Authors: Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL

from typing import Optional, Union

import neurokit2 as nk
import numpy as np

from ...api.decorators import register_marker
from ...utils import logger, warn_with_log
from .complexity_base import ComplexityBase


__all__ = ["SampleEntropy"]


@register_marker
class SampleEntropy(ComplexityBase):
    """Class for sample entropy of a time series.

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
        Parameters to pass to the sample entropy calculation function.
        For more information, check out
        ``junifer.markers.utils._sample_entropy``.
        If None, value is set to
        {"m": 2, "delay": 1, "tol": 0.5} (default None).
    name : str, optional
        The name of the marker. If None, it will use the class name
        (default None).

    Warnings
    --------
    This class is not automatically imported by junifer and requires you to
    import it explicitly. You can do it programmatically by
    ``from junifer.markers.complexity import SampleEntropy`` or in the YAML by
    ``with: junifer.markers.complexity``.

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
            self.params = {"m": 4, "delay": 1, "tol": 0.5}
        else:
            self.params = params

    def compute_complexity(
        self,
        extracted_bold_values: np.ndarray,
    ) -> np.ndarray:
        """Compute complexity measure.

        Take a timeseries of brain areas, and calculate sample entropy [1].

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
        .. [1] Richman, J., Moorman, J.
               Physiological time-series analysis using approximate entropy and
               sample entropy.
               Am. J. Physiol. Heart Circ. Physiol., 278 (6) (2000),
               pp. H2039-2049

        See Also
        --------
        neurokit2.entropy_sample

        """
        logger.info("Calculating sample entropy.")

        emb_dim = self.params["m"]
        delay = self.params["delay"]
        tol = self.params["tol"]

        assert isinstance(emb_dim, int), "Embedding dimension must be integer."
        assert isinstance(delay, int), "Delay must be integer."
        assert isinstance(tol, float), (
            "Tolerance must be a positive float number."
        )

        _, n_roi = extracted_bold_values.shape
        samp_en_roi = np.zeros((n_roi, 1))

        for idx_roi in range(n_roi):
            sig = extracted_bold_values[:, idx_roi]
            tol_corrected = tol * np.std(sig)
            tmp = nk.entropy_sample(
                sig, dimension=emb_dim, delay=delay, tolerance=tol_corrected
            )

            samp_en_roi[idx_roi] = tmp[0]

        if np.isnan(np.sum(samp_en_roi)):
            warn_with_log("There is NaN in the entropy values!")

        return samp_en_roi.T  # 1 X n_roi
