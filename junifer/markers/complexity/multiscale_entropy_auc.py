"""Provide class for the AUC of multiscale entropy of a time series."""

# Authors: Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL

from typing import Optional, Union

import neurokit2 as nk
import numpy as np

from ...api.decorators import register_marker
from ...utils import logger, warn_with_log
from .complexity_base import ComplexityBase


__all__ = ["MultiscaleEntropyAUC"]


@register_marker
class MultiscaleEntropyAUC(ComplexityBase):
    """Class for AUC of multiscale entropy of a time series.

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
        Parameters to pass to the AUC of multiscale entropy calculation
        function. For more information, check out
        ``junifer.markers.utils._multiscale_entropy_auc``. If None, value
        is set to {"m": 2, "tol": 0.5, "scale": 10} (default None).
    name : str, optional
        The name of the marker. If None, it will use the class name
        (default None).

    Warnings
    --------
    This class is not automatically imported by junifer and requires you to
    import it explicitly. You can do it programmatically by
    ``from junifer.markers.complexity import MultiscaleEntropyAUC`` or in the
    YAML by ``with: junifer.markers.complexity``.

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
            self.params = {"m": 2, "tol": 0.5, "scale": 10}
        else:
            self.params = params

    def compute_complexity(
        self,
        extracted_bold_values: np.ndarray,
    ) -> np.ndarray:
        """Compute complexity measure.

        Take a timeseries of brain areas, calculate multiscale entropy for each
        region and calculate the AUC of the entropy curves leading to a
        region-wise map of the brain [1].

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

        See Also
        --------
        neurokit2.entropy_multiscale

        """
        logger.info("Calculating AUC of multiscale entropy.")

        emb_dim = self.params["m"]
        tol = self.params["tol"]
        scale = self.params["scale"]

        assert isinstance(emb_dim, int), "Embedding dimension must be integer."
        assert isinstance(scale, int), "Scale must be integer."
        assert isinstance(
            tol, float
        ), "Tolerance must be a positive float number."

        _, n_roi = extracted_bold_values.shape
        MSEn_auc_roi = np.zeros((n_roi, 1))
        for idx_roi in range(n_roi):
            sig = extracted_bold_values[:, idx_roi]
            tol_corrected = tol * np.std(sig)
            tmp = nk.entropy_multiscale(
                sig,
                scale=scale,
                dimension=emb_dim,
                tolerance=tol_corrected,
                method="MSEn",
            )

            MSEn_auc_roi[idx_roi] = tmp[0]

        if np.isnan(np.sum(MSEn_auc_roi)):
            warn_with_log(
                "There is NaN in the entropy values, likely due "
                "to too short data length. A possible solution "
                "may be to choose a smaller value for 'scale'."
            )

        return MSEn_auc_roi.T  # 1 X n_roi
