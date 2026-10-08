"""Provide utility functions shared by different markers."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
#          Nicolás Nieto <n.nieto@fz-juelich.de>
#          Sami Hamdan <s.hamdan@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
#          Federico Raimondo <f.raimondo@fz-juelich.de>
#          Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
# License: AGPL

import zlib
from collections.abc import Callable
from typing import Any

import numpy as np
import pandas as pd
from nibabel.spatialimages import SpatialImage
from nilearn.image import get_data
from scipy.stats import zscore

from ..utils import raise_error


def _has_data(data: np.ndarray) -> np.ndarray:
    """Get the columns with data.

    Regions that are lost when resampling or warping the parcellation to the
    target image have no voxels, so their time series are all NaN.

    Parameters
    ----------
    data : np.ndarray
        The data (time x columns).

    Returns
    -------
    np.ndarray
        Boolean mask of the columns that are not all NaN.

    """
    return ~np.all(np.isnan(data), axis=0)


def _ets(
    bold_ts: np.ndarray,
    roi_names: list[str] | None = None,
) -> tuple[np.ndarray, list[str] | None]:
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
            "~".join([x, y])
            for x, y in zip(_roi_names[u], _roi_names[v], strict=False)
        ]
        return ets, edge_names


def _correlate_dataframes(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    method: str | Callable = "pearson",
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


def _checksum(array: np.ndarray) -> int | None:
    """Get the checksum of the values of an array.

    Parameters
    ----------
    array : numpy.ndarray
        The array.

    Returns
    -------
    int or None
        The CRC-32 of the bytes of the array, or None for arrays of objects.

    """
    if array.dtype.hasobject:
        return None
    return zlib.crc32(memoryview(np.ascontiguousarray(array)).cast("B"))


def _checksums(value: Any) -> tuple:
    """Get the checksums of an array, data frame or image.

    Parameters
    ----------
    value : Any
        The value.

    Returns
    -------
    tuple
        The checksums, empty for other values. For images: the affine, the
        data (loaded with nilearn, which caches it in the image, as most
        markers access it this way) and the data cached by nibabel's
        ``get_fdata`` (None if not cached).

    """
    if isinstance(value, np.ndarray):
        return (_checksum(value),)
    if isinstance(value, pd.DataFrame | pd.Series):
        return (_checksum(pd.util.hash_pandas_object(value).to_numpy()),)
    if isinstance(value, SpatialImage):
        fdata = getattr(value, "_fdata_cache", None)
        return (
            _checksum(value.affine),
            _checksum(get_data(value)),
            None if fdata is None else _checksum(fdata),
        )
    return ()


def _fingerprint(data: Any, path: tuple = ()) -> dict[tuple, tuple]:
    """Get a fingerprint of the data, to check whether it is changed.

    Parameters
    ----------
    data : Any
        The data.
    path : tuple, optional
        The keys leading to ``data`` (default ()).

    Returns
    -------
    dict
        For each path, the value (to check it is not replaced) and its
        checksums (to check it is not changed in place).

    """
    out = {path: (data, _checksums(data))}
    if isinstance(data, dict):
        for key, value in data.items():
            out.update(_fingerprint(value, (*path, key)))
    return out


def _is_changed(old: tuple, new: tuple) -> bool:
    """Check whether a value is changed.

    Parameters
    ----------
    old : tuple
        The value and its checksums before.
    new : tuple
        The value and its checksums after.

    Returns
    -------
    bool
        Whether the value was replaced or changed in place.

    """
    (old_value, old_sums), (new_value, new_sums) = old, new
    if new_value is not old_value:
        return True
    if isinstance(new_value, SpatialImage) and old_sums[2] is None:
        # The data cached by get_fdata during the computation cannot be
        # compared with its checksum, so compare it with the data
        fdata = getattr(new_value, "_fdata_cache", None)
        if fdata is not None and not np.array_equal(
            fdata, get_data(new_value), equal_nan=True
        ):
            return True
        old_sums, new_sums = old_sums[:2], new_sums[:2]
    return old_sums != new_sums


def _changed_paths(
    before: dict[tuple, tuple], after: dict[tuple, tuple]
) -> list[str]:
    """Get the paths of the data that are changed.

    Parameters
    ----------
    before : dict
        The fingerprint of the data before (see :func:`_fingerprint`).
    after : dict
        The fingerprint of the data after.

    Returns
    -------
    list of str
        The paths (keys joined by ".") that were added, removed, replaced or
        changed in place.

    """
    changed = [
        path
        for path in sorted(before.keys() | after.keys(), key=str)
        if path not in before
        or path not in after
        or _is_changed(before[path], after[path])
    ]
    return [".".join(str(key) for key in path) for path in changed]
