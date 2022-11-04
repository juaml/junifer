"""Provide utility functions shared by different markers."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
#          Nicolás Nieto <n.nieto@fz-juelich.de>
#          Sami Hamdan <s.hamdan@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import numpy as np
import pandas as pd
from scipy.stats import zscore


def _ets(bold_ts: np.ndarray) -> np.ndarray:
    """Compute the edge-wise time series based on BOLD time series.

    Take a timeseries of brain areas, and calculate timeseries for each
    edge according to the method outlined in [1]_. For more information,
    check https://github.com/brain-networks/edge-ts/blob/master/main.m

    Parameters
    ----------
    bold_ts : np.ndarray
        BOLD time series (time x ROIs)

    Returns
    -------
    np.ndarray
        edge-wise time series, i.e. estimate of functional connectivity at each
        time point.

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
    return timeseries[:, u] * timeseries[:, v]


def _correlate_dataframes(df1, df2, method="pearson"):
    """Column-wise correlations between two dataframes.

    Correlates each column from dataframe 1 with each column from dataframe 2.
    Output is a dataframe of shape (df2.shape[1], df1.shape[1]).
    It is required that number of rows are matched.

    Parameters
    ----------
    df1 : pd.DataFrame
    df2 : pd.DataFrame
    method : str or callable
        any method that can be passed to:
        https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.corr.html

    Returns :
    ---------
    df_corr : pd.DataFrame
    """

    assert (
        df1.shape[0] == df2.shape[0]
    ), "pd.DataFrames have unequal number of rows!"
    return (
        pd.concat([df1, df2], axis=1, keys=["df1", "df2"])
        .corr(method=method)
        .loc["df2", "df1"]
    )
