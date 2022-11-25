"""Provide utility functions shared by different markers."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
#          Nicolás Nieto <n.nieto@fz-juelich.de>
#          Sami Hamdan <s.hamdan@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
#          Federico Raimondo <f.raimondo@fz-juelich.de>
#          Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
# License: AGPL

from typing import Callable, List, Optional, Tuple, Union

import neurokit2 as nk
import numpy as np
import pandas as pd

# from ptpython.repl import embed
from scipy.stats import zscore

from ..utils import raise_error, warn_with_log


def _ets(
    bold_ts: np.ndarray,
    roi_names: Union[None, List[str]] = None,
) -> Tuple[np.ndarray, Optional[List[str]]]:
    """Compute the edge-wise time series based on BOLD time series.

    Take a timeseries of brain areas, and calculate timeseries for each
    edge according to the method outlined in [1]_. For more information,
    check https://github.com/brain-networks/edge-ts/blob/master/main.m

    Parameters
    ----------
    bold_ts : np.ndarray
        BOLD time series (time x ROIs)
    roi_names : List[str] or None
        List containing the names of the ROIs.
        Order of the ROI names should correspond to order of the columns
        in bold_ts. If None (default), only the edge-wise time series are
        returned, without corresponding edge labels.

    Returns
    -------
    ets : np.ndarray
        edge-wise time series, i.e. estimate of functional connectivity at each
        time point.
    edge_names : List[str]
        List of edge names corresponding to columns in the edge-wise time
        series. If roi_names are not specified, this is None.

    References
    ----------
    .. [1] Zamani Esfahlani et al. (2020)
            High-amplitude cofluctuations in cortical activity drive
            functional connectivity
            doi: 10.1073/pnas.2005531117

    """
    # Compute the z-score for each brain region's timeseries
    timeseries = zscore(bold_ts)
    # Get the number of ROIs
    _, n_roi = timeseries.shape
    # indices of unique edges (lower triangle)
    u, v = np.tril_indices(n_roi, k=-1)
    # Compute the ETS
    ets = timeseries[:, u] * timeseries[:, v]
    # Obtain the corresponding edge labels if specified else return
    if roi_names is None:
        return ets, None
    else:
        if len(roi_names) != n_roi:
            raise_error(
                "List of roi names does not correspond "
                "to the number of ROIs in the timeseries!"
            )
        _roi_names = np.array(roi_names)
        edge_names = [
            "~".join([x, y]) for x, y in zip(_roi_names[u], _roi_names[v])
        ]
        return ets, edge_names


def _correlate_dataframes(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    method: Union[str, Callable] = "pearson",
) -> pd.DataFrame:
    """Column-wise correlations between two dataframes.

    Correlates each column of `df1` with each column of `df2`.
    Output is a dataframe of shape (df2.shape[1], df1.shape[1]).
    It is required that number of rows are matched.

    Parameters
    ----------
    df1 : pandas.DataFrame
        The first dataframe.
    df2 : pandas.DataFrame
        The second dataframe.
    method : str or callable, optional
        any method that can be passed to
        :func:`pandas.DataFrame.corr` (default "pearson").

    Returns
    -------
    df_corr : pandas.DataFrame
        The correlated values as a dataframe.

    Raises
    ------
    ValueError
        If number of rows between dataframes are not matched.

    """

    if df1.shape[0] != df2.shape[0]:
        raise_error("pandas.DataFrame's have unequal number of rows!")
    return (
        pd.concat([df1, df2], axis=1, keys=["df1", "df2"])  # type: ignore
        .corr(method=method)  # type: ignore
        .loc["df2", "df1"]
    )


def _calculate_complexity(
    bold_ts: np.ndarray,
    measure_type: dict,
) -> np.ndarray:
    """Compute the region-wise complexity measures from 2d BOLD time series.

    Available options and their default values:

    {"_range_entropy": {"m": 2, "tol": 0.5}}
    {"_range_entropy_auc": {"m": 2, "n_r": 10}}
    {"_perm_entropy": {"m": 4, "tau": 1}}
    {"_weighted_perm_entropy": {"m": 4, "tau": 1}}
    {"_sample_entropy": {"m": 2, "tau": 1, "tol": 0.5}}
    {"_multiscale_entropy_auc": {"m": 2, "tol": 0.5, "scale": 10}}
    {"_hurst_exponent": {"reserved": None}}

    - Range entropy: Take a timeseries of brain areas, and calculate
      range entropy according to the method outlined in [1].

    - AUC of range entropy: Compute range entropy of the timeseries over
      the r-interval of 0 to 1 and calculat its area under the curve as a
      complexity measure.

    - Permutation entropy: Take a timeseries of brain areas, and calculate
      permutation entropy according to the method outlined in [2].

    - Weighted permutation entropy: Take a timeseries of brain areas, and
      calculate permutation entropy according to the method outlined in [3].

    - Sample entropy: Take a timeseries of brain areas, and calculate
      sample entropy [4].

    - Multiscale entropy: Take a timeseries of brain areas, calculate
      multiscale entropy for each region and calculate the AUC of the entropy
      curves leading to a region-wise map of the brain [5].

    - Hurst exponent: Take a timeseries of brain areas, and calculate
      Hurst exponent using the detrended fluctuation analysis method assuming
      the data is monofractal (q = 2 in nk.fractal_dfa) [6].

    Parameters
    ----------
    bold_ts : np.ndarray
        BOLD time series (time x ROIs)

    Returns
    -------
    np.ndarray
        ROI-wise brain map, i.e. estimate of range entropy at each ROI.

    References
    ----------
    .. [1] Omidvarnia, A., et al.
           Range Entropy: A Bridge between Signal Complexity and
           Self-Similarity, Entropy, vol. 20, no. 12, p. 962, 2018.

    .. [2] Bandt, C., & Pompe, B.
           Permutation entropy: a natural complexity measure for time
           series. Physical review letters, 88(17), 174102, 2002.

    .. [3] Fadlallah, B., et al.
           Weighted-permutation entropy: A complexity measure for time series
           incorporating amplitude information.
           Physical Review E, 87(2), 022911, 2013.

    .. [4] Richman, J., Moorman, J.
           Physiological time-series analysis using approximate entropy and
           sample entropy, Am. J. Physiol. Heart Circ. Physiol.,
           278 (6), pp. H2039-2049, 2000.

    .. [5] Costa, M., Goldberger, A. L., & Peng, C. K.
           Multiscale entropy analysis of complex physiologic time series.
           Physical review letters, 89(6), 068102, 2002.

    .. [6] Peng, C.; Havlin, S.; Stanley, H.E.; Goldberger, A.L.
           Quantification of scaling exponents and crossover phenomena in
           nonstationary heartbeat time series.
           Chaos Interdiscip. J. Nonlinear Sci., 5, 82–87, 1995.

    See also
    ---------
    https://neuropsychology.github.io/NeuroKit/functions/complexity.html

    """
    # print('Stop: _calculate_complexity')
    # embed(globals(), locals())

    # Start the analysis
    complexity_measure = list(measure_type.keys())[0]
    params = list(measure_type.values())[0]
    func_name = globals()[complexity_measure]
    feature_map = func_name(bold_ts, params)  # n_roi x 1
    complexity_features = feature_map.T

    return complexity_features


def _range_entropy(bold_ts: np.ndarray, params: dict) -> np.ndarray:
    """Compute the region-wise range entropy from 2d BOLD time series.

    - Range entropy: Take a timeseries of brain areas, and calculate
      range entropy according to the method outlined in [1].

    Parameters
    ----------
    bold_ts : np.ndarray
        BOLD time series (time x ROIs)
    params : dict
        The dictionary of input parameters.

    Returns
    -------
    range_en_roi: np.ndarray
        ROI-wise brain map of range entropy.

    References
    ----------
    .. [1] A. Omidvarnia et al. (2018)
           Range Entropy: A Bridge between Signal Complexity and
           Self-Similarity, Entropy, vol. 20, no. 12, p. 962.

    See also
    ---------
    https://neuropsychology.github.io/NeuroKit/functions/complexity.html

    """
    # print('Stop: _range_entropy')
    # embed(globals(), locals())

    emb_dim = params["m"]
    tolerance = params["tol"]
    _, n_roi = bold_ts.shape
    range_en_roi = np.zeros((n_roi, 1))

    for idx_roi in range(n_roi):
        sig = bold_ts[:, idx_roi]
        tmp = nk.entropy_range(
            sig, dimension=emb_dim, tolerance=tolerance, method="mSampEn"
        )
        range_en_roi[idx_roi] = tmp[0]

    if np.isnan(np.sum(range_en_roi)):
        warn_with_log("There is NaN in the entropy values!")

    return range_en_roi


def _range_entropy_auc(bold_ts: np.ndarray, params: dict) -> np.ndarray:
    """Compute the region-wise AUC of range entropy from 2d BOLD time series.

    - AUC of range entropy: Take a timeseries of brain areas, calculate
      range entropy according to the method outlined in [1] across the range
      of tolerance value r from 0 to 1, and compute its area under the curve.

    Parameters
    ----------
    bold_ts : np.ndarray
        BOLD time series (time x ROIs)
    params : dict
        The dictionary of input parameters.

    Returns
    -------
    range_en_auc_roi: np.ndarray
        ROI-wise brain map of range entropy.

    References
    ----------
    .. [1] A. Omidvarnia et al. (2018)
           Range Entropy: A Bridge between Signal Complexity and
           Self-Similarity, Entropy, vol. 20, no. 12, p. 962.

    See also
    ---------
    https://neuropsychology.github.io/NeuroKit/functions/complexity.html

    """
    # print('Stop: _range_entropy_auc')
    # embed(globals(), locals())

    emb_dim = params["m"]
    n_r = params["n_r"]
    r_span = np.arange(1 / n_r, (1 + 1 / n_r), 1 / n_r)  # Tolerance r span
    _, n_roi = bold_ts.shape
    range_en_auc_roi = np.zeros((n_roi, 1))

    for idx_roi in range(n_roi):

        sig = bold_ts[:, idx_roi]

        range_en_roi_tmp = np.zeros((n_r, 1))
        r_idx = 0
        for tolerance in r_span:
            tmp = nk.entropy_range(
                sig, dimension=emb_dim, tolerance=tolerance, method="mSampEn"
            )
            range_en_roi_tmp[r_idx] = tmp[0]
            r_idx = r_idx + 1

        tmp = np.trapz(range_en_roi_tmp.T)
        range_en_auc_roi[idx_roi] = tmp / n_r

    if np.isnan(np.sum(range_en_auc_roi)):
        warn_with_log(
            (
                "There is NaN in the entropy values, likely "
                "due to an unnecessarily large n_r. The recommended "
                "value is n_r = 10."
            )
        )

    return range_en_auc_roi


def _perm_entropy(bold_ts: np.ndarray, params: dict) -> np.ndarray:
    """Compute the region-wise permutation entropy from 2d BOLD time series.

    - Permutation entropy: Take a timeseries of brain areas, and calculate
      permutation entropy according to the method outlined in [1].

    Parameters
    ----------
    bold_ts : np.ndarray
        BOLD time series (time x ROIs)
    params : dict
        The dictionary of input parameters.

    Returns
    -------
    perm_en_roi: np.ndarray
        ROI-wise brain map of permutation entropy.

    References
    ----------
    .. [1] Bandt, C., & Pompe, B. (2002)
           Permutation entropy: a natural complexity measure for time
           series. Physical review letters, 88(17), 174102.

    See also
    ---------
    https://neuropsychology.github.io/NeuroKit/functions/complexity.html

    """
    # print('Stop: _perm_entropy')
    # embed(globals(), locals())

    emb_dim = params["m"]
    delay = params["tau"]
    _, n_roi = bold_ts.shape
    perm_en_roi = np.zeros((n_roi, 1))

    for idx_roi in range(n_roi):
        sig = bold_ts[:, idx_roi]
        tmp = nk.entropy_permutation(
            sig,
            dimension=emb_dim,
            delay=delay,
            weighted=False,  # PE, not wPE
            corrected=True,  # Normalized PE
        )

        perm_en_roi[idx_roi] = tmp[0]

    if np.isnan(np.sum(perm_en_roi)):
        warn_with_log("There is NaN in the entropy values!")

    return perm_en_roi


def _weighted_perm_entropy(bold_ts: np.ndarray, params: dict) -> np.ndarray:
    """Compute the region-wise weighted permutation entropy from bold_ts.

    - Weighted permutation entropy: Take a timeseries of brain areas, and
      calculate weighted permutation entropy according to the method
      outlined in [1].

    Parameters
    ----------
    bold_ts : np.ndarray
        BOLD time series (time x ROIs)
    params : dict
        The dictionary of input parameters.

    Returns
    -------
    w_perm_en_roi: np.ndarray
        ROI-wise brain map of weighted permutation entropy.

    References
    ----------
    .. [1] Fadlallah, B., Chen, B., Keil, A., & Principe, J. (2013)
           Weighted-permutation entropy: A complexity measure for time series
           incorporating amplitude information.
           Physical Review E, 87(2), 022911.

    See also
    ---------
    https://neuropsychology.github.io/NeuroKit/functions/complexity.html

    """
    # print('Stop: _weighted_perm_entropy')
    # embed(globals(), locals())

    emb_dim = params["m"]
    delay = params["tau"]
    _, n_roi = bold_ts.shape
    wperm_en_roi = np.zeros((n_roi, 1))

    for idx_roi in range(n_roi):
        sig = bold_ts[:, idx_roi]
        tmp = nk.entropy_permutation(
            sig,
            dimension=emb_dim,
            delay=delay,
            weighted=True,  # Weighted PE
            corrected=True,  # Normalized PE
        )

        wperm_en_roi[idx_roi] = tmp[0]

    if np.isnan(np.sum(wperm_en_roi)):
        warn_with_log("There is NaN in the entropy values!")

    return wperm_en_roi


def _sample_entropy(bold_ts: np.ndarray, params: dict) -> np.ndarray:
    """Compute the region-wise weighted permutation entropy from bold_ts.

    - Sample entropy: Take a timeseries of brain areas, and
      calculate sample entropy [1].

    Parameters
    ----------
    bold_ts : np.ndarray
        BOLD time series (time x ROIs)
    params : dict
        The dictionary of input parameters.

    Returns
    -------
    samp_en_roi: np.ndarray
        ROI-wise brain map of sample entropy.

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
    # print('Stop: _sample_entropy')
    # embed(globals(), locals())

    emb_dim = params["m"]
    delay = params["tau"]
    tol = params["tol"]

    _, n_roi = bold_ts.shape
    samp_en_roi = np.zeros((n_roi, 1))

    for idx_roi in range(n_roi):
        sig = bold_ts[:, idx_roi]
        tol_corrected = tol * np.std(sig)
        tmp = nk.entropy_sample(
            sig, dimension=emb_dim, delay=delay, tolerance=tol_corrected
        )

        samp_en_roi[idx_roi] = tmp[0]

    if np.isnan(np.sum(samp_en_roi)):
        warn_with_log("There is NaN in the entropy values!")

    return samp_en_roi


def _multiscale_entropy_auc(bold_ts: np.ndarray, params: dict) -> np.ndarray:
    """Compute the region-wise AUC of multiscale entropy of bold_ts.

    - Multiscale entropy: Take a timeseries of brain areas,
      calculate multiscale entropy for each region and calculate the AUC
      of the entropy curves leading to a region-wise map of the brain [1].

    Parameters
    ----------
    bold_ts : np.ndarray
        BOLD time series (time x ROIs)
    params : dict
        The dictionary of input parameters.

    Returns
    -------
    hurst_roi: np.ndarray
        ROI-wise brain map of the AUC of multiscale entropy.

    References
    ----------
    .. [1] Costa, M., Goldberger, A. L., & Peng, C. K.
           Multiscale entropy analysis of complex physiologic time series.
           Physical review letters, 89(6), 068102, 2002.

    See also
    ---------
    https://neuropsychology.github.io/NeuroKit/functions/complexity.html

    """
    # print('Stop: _multiscale_entropy_auc')
    # embed(globals(), locals())

    emb_dim = params["m"]
    tol = params["tol"]
    scale = params["scale"]

    _, n_roi = bold_ts.shape
    MSEn_auc_roi = np.zeros((n_roi, 1))
    for idx_roi in range(n_roi):
        sig = bold_ts[:, idx_roi]
        tol_corrected = tol * np.std(sig)
        tmp = nk.entropy_multiscale(
            sig,
            scale=scale,
            dimension=emb_dim,
            tolerance=tol_corrected,
            fuzzy=False,  # Not Fuzzy entropy
            refined=False,  # Not refined version
            show=False,
        )

        MSEn_auc_roi[idx_roi] = tmp[0]

    if np.isnan(np.sum(MSEn_auc_roi)):
        warn_with_log(
            (
                "There is NaN in the entropy values, likely due "
                "to too short data length. A possible solution "
                "may be to choose a smaller value for 'scale'."
            )
        )

    return MSEn_auc_roi


def _hurst_exponent(bold_ts: np.ndarray, params: dict) -> np.ndarray:
    """Compute the region-wise Hurst exponent of bold_ts.

    - Hurst exponent: Take a timeseries of brain areas, and
      calculate Hurst exponent using the detrended fluctuation analysis
      method assuming the data is monofractal (q = 2 in nk.fractal_dfa) [1].

    Parameters
    ----------
    bold_ts : np.ndarray
        BOLD time series (time x ROIs)
    params : dict
        The dictionary of input parameters.

    Returns
    -------
    hurst_roi: np.ndarray
        ROI-wise brain map of Hurst exponent.

    References
    ----------
    .. [1] Peng, C.; Havlin, S.; Stanley, H.E.; Goldberger, A.L.
           Quantification of scaling exponents and crossover phenomena in
           nonstationary heartbeat time series.
           Chaos Interdiscip. J. Nonlinear Sci., 5, 82–87, 1995

    See also
    ---------
    https://neuropsychology.github.io/NeuroKit/functions/complexity.html

    """
    # print('Stop: _hurst_exponent')
    # embed(globals(), locals())

    _, n_roi = bold_ts.shape
    hurst_roi = np.zeros((n_roi, 1))

    for idx_roi in range(n_roi):
        sig = bold_ts[:, idx_roi]
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

    if np.isnan(np.sum(hurst_roi)):
        warn_with_log("There is NaN in the Hurst exponent values!")

    return hurst_roi
