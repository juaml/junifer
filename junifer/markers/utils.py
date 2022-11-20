"""Provide utility functions shared by different markers."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
#          Nicolás Nieto <n.nieto@fz-juelich.de>
#          Sami Hamdan <s.hamdan@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
#          Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from typing import Callable, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy.stats import zscore
import neurokit2 as nk

from ..utils import raise_error


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
    feature_kinds: dict,
    ) -> np.ndarray:
    """Compute the region-wise complexity measures from 2d BOLD time series.

    - Permutation entropy: Take a timeseries of brain areas, and calculate
      permutation entropy according to the method outlined in [1].

    - Range entropy: Take a timeseries of brain areas, and calculate
      range entropy according to the method outlined in [2].

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
    .. [1] A. Omidvarnia et al. (2018)
           Range Entropy: A Bridge between Signal Complexity and
           Self-Similarity, Entropy, vol. 20, no. 12, p. 962, 2018.

    .. [2] A. Omidvarnia et al. (2018)
           Range Entropy: A Bridge between Signal Complexity and
           Self-Similarity, Entropy, vol. 20, no. 12, p. 962, 2018.

    """
    _, n_roi = bold_ts.shape

    # Number of complexity measures to be computed.
    n_feat = len(feature_kinds)

    # Initialize the matrix of all feature maps for bold_ts
    complexity_features = np.zeros((n_roi, n_feat))

    # Start the analysis
    feat_idx = 0
    for feature, feature_params in feature_kinds.items():
        func = feature_kinds[feature]  # Complexity measure (function name)
        feature_map = func(bold_ts, **feature_params) # n_roi x 1
        complexity_features[:, feat_idx] = feature_map
        feat_idx = feat_idx + 1

    return complexity_features

def _range_entropy(
    bold_ts: np.ndarray,
    feature_kinds: dict
    ) -> np.ndarray:
    """Compute the region-wise range entropy from 2d BOLD time series.

    - Range entropy: Take a timeseries of brain areas, and calculate
      range entropy according to the method outlined in [1].

    Parameters
    ----------
    bold_ts : np.ndarray
        BOLD time series (time x ROIs)
    feature_kinds : dict
        a dctionary with keys as the function names, and values as another 
        dictionary with function parameters.

    Returns
    -------
    range_en_roi: np.ndarray
        ROI-wise brain map of range entropy.

    References
    ----------
    .. [1] A. Omidvarnia et al. (2018)
           Range Entropy: A Bridge between Signal Complexity and
           Self-Similarity, Entropy, vol. 20, no. 12, p. 962, 2018.

    """
    params =  feature_kinds["_range_entropy"]
    emb_dim = params["m"]
    tolerance = params["tol"]
    _, n_roi = bold_ts.shape
    range_en_roi = np.zeros((n_roi, 1))

    for idx_roi in range(n_roi):
        sig = bold_ts[:, idx_roi]
        range_en_roi[idx_roi] = nk.entropy_range(
            sig,
            dimension = emb_dim,
            tolerance = tolerance,
            approximate = False  # RangeEn B
        )
        
    return range_en_roi


def _range_entropy_auc(
    bold_ts: np.ndarray,
    feature_kinds: dict
    ) -> np.ndarray:
    """Compute the region-wise AUC of range entropy from 2d BOLD time series.

    - AUC of range entropy: Take a timeseries of brain areas, calculate
      range entropy according to the method outlined in [1] across the range
      of tolerance value r from 0 to 1, and compute its area under the curve.

    Parameters
    ----------
    bold_ts : np.ndarray
        BOLD time series (time x ROIs)
    feature_kinds : dict
        a dctionary with keys as the function names, and values as another 
        dictionary with function parameters.

    Returns
    -------
    range_en_auc_roi: np.ndarray
        ROI-wise brain map of range entropy.

    References
    ----------
    .. [1] A. Omidvarnia et al. (2018)
           Range Entropy: A Bridge between Signal Complexity and
           Self-Similarity, Entropy, vol. 20, no. 12, p. 962, 2018.

    """
    params =  feature_kinds["_range_entropy"]
    emb_dim = params["m"]
    n_r = params["n_r"]
    r_span = np.arange(0, 1, 1/n_r)  # Tolerance r span
    _, n_roi = bold_ts.shape
    range_en_auc_roi = np.zeros((n_roi, 1))

    for idx_roi in range(n_roi):
        sig = bold_ts[:, idx_roi]

        for tolerance in r_span:
            range_en_auc_roi_tmp = nk.entropy_range(
                sig,
                dimension = emb_dim,
                tolerance = tolerance,
                approximate = False  # RangeEn B
            )

        range_en_auc_roi[idx_roi] = np.trapz(range_en_auc_roi_tmp)
        
    return range_en_auc_roi


def _perm_entropy(
    bold_ts: np.ndarray,
    feature_kinds: dict
    ) -> np.ndarray:
    """Compute the region-wise permutation entropy from 2d BOLD time series.

    - Permutation entropy: Take a timeseries of brain areas, and calculate
      permutation entropy according to the method outlined in [1].

    Parameters
    ----------
    bold_ts : np.ndarray
        BOLD time series (time x ROIs)
    feature_kinds : dict
        a dctionary with keys as the function names, and values as another 
        dictionary with function parameters.

    Returns
    -------
    perm_en_roi: np.ndarray
        ROI-wise brain map of permutation entropy.

    References
    ----------
    .. [1] Bandt, C., & Pompe, B. (2002)
           Permutation entropy: a natural complexity measure for time
           series. Physical review letters, 88(17), 174102.

    """
    params =  feature_kinds["_perm_entropy"]
    emb_dim = params["m"]
    delay = params["tau"]
    _, n_roi = bold_ts.shape
    perm_en_roi = np.zeros((n_roi, 1))

    for idx_roi in range(n_roi):
        sig = bold_ts[:, idx_roi]
        perm_en_roi[idx_roi] = nk.entropy_permutation(
            sig,
            dimension = emb_dim,
            delay = delay,
            weighted = False,  # PE, not wPE
            corrected = True  # Normalized PE
        )
        
    return perm_en_roi


def _weighetd_perm_entropy(
    bold_ts: np.ndarray,
    feature_kinds: dict
    ) -> np.ndarray:
    """Compute the region-wise weighted permutation entropy
    from 2d BOLD time series.

    - Weighted permutation entropy: Take a timeseries of brain areas, and
      calculate weighted permutation entropy according to the method
      outlined in [1].

    Parameters
    ----------
    bold_ts : np.ndarray
        BOLD time series (time x ROIs)
    feature_kinds : dict
        a dctionary with keys as the function names, and values as another 
        dictionary with function parameters.

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

    """
    params =  feature_kinds["_weighted_perm_entropy"]
    emb_dim = params["m"]
    delay = params["tau"]
    _, n_roi = bold_ts.shape
    wperm_en_roi = np.zeros((n_roi, 1))

    for idx_roi in range(n_roi):
        sig = bold_ts[:, idx_roi]
        wperm_en_roi[idx_roi] = nk.entropy_permutation(
            sig,
            dimension = emb_dim,
            delay = delay,
            weighted = True,  # Weighted PE
            corrected = True  # Normalized PE
        )
        
    return wperm_en_roi

