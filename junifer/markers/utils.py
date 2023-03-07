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
def _weighted_perm_entropy(bold_ts: np.ndarray, params: Dict) -> np.ndarray:
    """Compute the region-wise weighted permutation entropy of BOLD timeseries.

    Take a timeseries of brain areas, and calculate weighted permutation
    entropy according to the method outlined in [1].

    Parameters
    ----------
    bold_ts : np.ndarray
        BOLD time series (time x ROIs).
    params : dict
        The dictionary of input parameters.

    Returns
    -------
    np.ndarray
        ROI-wise brain map of weighted permutation entropy.

    References
    ----------
    .. [1] Fadlallah, B., Chen, B., Keil, A., & Principe, J. (2013)
           Weighted-permutation entropy: A complexity measure for time series
           incorporating amplitude information.
           Physical Review E, 87(2), 022911.

    See also
    --------
    https://neuropsychology.github.io/NeuroKit/functions/complexity.html

    """
    emb_dim = params["m"]
    delay = params["delay"]

    assert isinstance(emb_dim, int), "Embedding dimension must be integer."
    assert isinstance(delay, int), "Delay must be integer."

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

    wperm_en_roi = wperm_en_roi.T  # 1 X n_roi

    return wperm_en_roi


