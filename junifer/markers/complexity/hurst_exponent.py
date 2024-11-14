"""Provide class for Hurst exponent of a time series."""

# Authors: Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL

from typing import Optional, Union

import neurokit2 as nk
import numpy as np

from ...api.decorators import register_marker
from ...utils import logger, warn_with_log
from .complexity_base import ComplexityBase


__all__ = ["HurstExponent"]


@register_marker
class HurstExponent(ComplexityBase):
    """Class for Hurst exponent of a time series.

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
        Parameters to pass to the Hurst exponent calculation function. For more
        information, check out ``junifer.markers.utils._hurst_exponent``.
        If None, value is set to {"method": "dfa"} (default None).
    name : str, optional
        The name of the marker. If None, it will use the class name
        (default None).

    Warnings
    --------
    This class is not automatically imported by junifer and requires you to
    import it explicitly. You can do it programmatically by
    ``from junifer.markers.complexity import HurstExponent`` or in the YAML by
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
            self.params = {"method": "dfa"}
        else:
            self.params = params

    def compute_complexity(
        self,
        extracted_bold_values: np.ndarray,
    ) -> np.ndarray:
        """Compute complexity measure.

        Take a timeseries of brain areas, and calculate Hurst exponent using
        the detrended fluctuation analysis method assuming the data is
        monofractal [1].

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
        .. [1] Peng, C.; Havlin, S.; Stanley, H.E.; Goldberger, A.L.
               Quantification of scaling exponents and crossover phenomena in
               nonstationary heartbeat time series.
               Chaos Interdiscip. J. Nonlinear Sci., 5, 82-87, 1995.

        See Also
        --------
        neurokit2.fractal_dfa

        """
        logger.info(f"Calculating Hurst exponent ({self.params['method']}).")

        _, n_roi = extracted_bold_values.shape
        hurst_roi = np.zeros((n_roi, 1))

        if self.params["method"] == "dfa":
            for idx_roi in range(n_roi):
                sig = extracted_bold_values[:, idx_roi]
                tmp = nk.fractal_dfa(
                    sig,
                    scale="default",
                    overlap=True,
                    integrate=True,
                    order=1,
                    multifractal=False,
                    q="default",  # q = 2 for monofractal Hurst exponent
                    maxdfa=False,
                    show=False,
                )

                hurst_roi[idx_roi] = tmp[0]

        else:
            hurst_roi = np.empty((n_roi, 1))
            hurst_roi[:] = np.nan
            warn_with_log("The DFA method is available only!")

        if np.isnan(np.sum(hurst_roi)):
            warn_with_log("There is NaN in the Hurst exponent values!")

        return hurst_roi.T  # 1 X n_roi
