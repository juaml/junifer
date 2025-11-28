"""Provide class for permutation entropy of a time series."""

# Authors: Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Optional

import neurokit2 as nk
import numpy as np

from ...api.decorators import register_marker
from ...utils import logger, warn_with_log
from .complexity_base import ComplexityBase


__all__ = ["PermEntropy"]


@register_marker
class PermEntropy(ComplexityBase):
    """Class for permutation entropy of a time series.

    Parameters
    ----------
    parcellation : str or list of str
        The name(s) of the parcellation(s) to use.
        See :func:`.list_data` for options.
    agg_method : str, optional
        The aggregation function to use.
        See :func:`.get_aggfunc_by_name` for options
        (default "mean").
    agg_method_params : dict or None, optional
        The parameters to pass to the aggregation function.
        See :func:`.get_aggfunc_by_name` for options (default None).
    masks : str, dict, list of them or None, optional
        The specification of the masks to apply to regions before extracting
        signals. Check :ref:`Using Masks <using_masks>` for more details.
        If None, will not apply any mask (default None).
    params : dict or None, optional
        The parameters to pass to the permutation entropy calculation function.
        See ``junifer.markers.utils._perm_entropy`` for more information.
        If None, value is set to ``{"m": 2, "delay": 1}`` (default None).
    name : str or None, optional
        The name of the marker.
        If None, will use the class name (default None).

    Warnings
    --------
    This class is not automatically imported by junifer and requires you to
    import it explicitly. You can do it programmatically by
    ``from junifer.markers.complexity import PermEntropy`` or in the YAML by
    ``with: junifer.markers.complexity``.

    """

    params: Optional[dict] = None

    def validate_marker_params(self) -> None:
        """Run extra logical validation for marker."""
        if self.params is None:
            self.params = {"m": 4, "delay": 1}

    def compute_complexity(
        self,
        extracted_bold_values: np.ndarray,
    ) -> np.ndarray:
        """Compute complexity measure.

        Take a timeseries of brain areas, and calculate permutation entropy
        according to the method outlined in [1].

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
        .. [1] Bandt, C., & Pompe, B. (2002)
               Permutation entropy: a natural complexity measure for time
               series.
               Physical review letters, 88(17), 174102.

        See Also
        --------
        neurokit2.entropy_permutation

        """
        logger.info("Calculating permutation entropy.")

        emb_dim = self.params["m"]
        delay = self.params["delay"]

        assert isinstance(emb_dim, int), "Embedding dimension must be integer."
        assert isinstance(delay, int), "Delay must be integer."

        _, n_roi = extracted_bold_values.shape
        perm_en_roi = np.zeros((n_roi, 1))

        for idx_roi in range(n_roi):
            sig = extracted_bold_values[:, idx_roi]
            tmp = nk.entropy_permutation(
                sig,
                dimension=emb_dim,
                delay=delay,
                weighted=False,  # PE, not wPE
                corrected=True,  # Normalized PE
            )

            perm_en_roi[idx_roi] = tmp[0]

        if np.isnan(np.sum(perm_en_roi)):
            warn_with_log("There is NaN in the permutation entropy values!")

        return perm_en_roi.T  # 1 X n_roi
