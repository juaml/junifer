"""Provide utility functions shared by different markers."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
#          Nicolás Nieto <n.nieto@fz-juelich.de>
#          Sami Hamdan <s.hamdan@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
#          Federico Raimondo <f.raimondo@fz-juelich.de>
#          Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
# License: AGPL

import hashlib
import zlib
from collections.abc import Callable
from pathlib import Path
from typing import Any

import nibabel as nib
import numpy as np
import pandas as pd
from nibabel.spatialimages import SpatialImage
from scipy.stats import zscore

from ..pipeline import WorkDirManager
from ..utils import raise_error


def _save_mask(mask_img: SpatialImage, prefix: str) -> Path:
    """Save mask to the element directory, named by its content.

    The same mask always gets the same path within an element, so that the
    cached computations (e.g., ReHo or ALFF) can be reused by markers using
    the same mask. The element directory is deleted after the element is
    processed.

    Parameters
    ----------
    mask_img : Niimg-like object
        The mask to save.
    prefix : str
        The prefix of the file name.

    Returns
    -------
    pathlib.Path
        The path to the saved mask.

    """
    mask_data = np.squeeze(np.asarray(mask_img.dataobj)) != 0
    digest = hashlib.sha256()
    digest.update(str(mask_data.shape).encode())
    digest.update(np.packbits(mask_data).tobytes())
    digest.update(mask_img.affine.tobytes())
    mask_path = (
        WorkDirManager().get_elementdir()
        / f"{prefix}_{digest.hexdigest()[:16]}.nii"
    )
    if not mask_path.exists():
        nib.save(
            nib.Nifti1Image(
                mask_data.astype(np.uint8), mask_img.affine, mask_img.header
            ),
            mask_path,
        )
    return mask_path


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


def _checksum(array: np.ndarray) -> tuple:
    """Get the checksum of an array.

    Parameters
    ----------
    array : numpy.ndarray
        The array.

    Returns
    -------
    tuple
        The shape, the dtype and the CRC-32 of the bytes of the array (None
        for arrays of objects).

    """
    crc = None
    if not array.dtype.hasobject:
        # The transpose of an array in Fortran order (e.g., the data of a
        # NIfTI image) is in C order, so it is not copied
        if array.flags.f_contiguous and not array.flags.c_contiguous:
            array = array.T
        crc = zlib.crc32(memoryview(np.ascontiguousarray(array)).cast("B"))
    return (array.shape, array.dtype.str, crc)


def _image_data(img: SpatialImage) -> tuple:
    """Get the data of an image in memory.

    The data read from the file of an image is not loaded, as it cannot be
    changed (unless it is cached) and it would be kept in memory.

    Parameters
    ----------
    img : nibabel.spatialimages.SpatialImage
        The image.

    Returns
    -------
    tuple
        The data of the image if it is in memory (the data of an image
        created from an array, or the data cached by nilearn, e.g., with
        ``nilearn.image.get_data``) and the data cached by nibabel's
        ``get_fdata``, or None.

    """
    data = img.dataobj
    if not isinstance(data, np.ndarray):
        data = getattr(img, "_data_cache", None)
    return data, getattr(img, "_fdata_cache", None)


def _checksums(value: Any) -> tuple:
    """Get the checksums of an array, data frame, image or set.

    Parameters
    ----------
    value : Any
        The value.

    Returns
    -------
    tuple
        The checksums, empty for other values. For data frames and series:
        the values and index, and the column labels or name. For images: the
        affine and the data in memory (see :func:`_image_data`, None if not in
        memory). For sets: their contents.

    """
    if isinstance(value, np.ndarray):
        return (_checksum(value),)
    if isinstance(value, pd.DataFrame | pd.Series):
        labels = (
            tuple(value.columns)
            if isinstance(value, pd.DataFrame)
            else value.name
        )
        return (
            _checksum(pd.util.hash_pandas_object(value).to_numpy()),
            labels,
        )
    if isinstance(value, SpatialImage):
        return (
            _checksum(value.affine),
            *(
                None if data is None else _checksum(data)
                for data in _image_data(value)
            ),
        )
    if isinstance(value, set | frozenset):
        return (frozenset(value),)
    return ()


def _fingerprint(data: Any, path: tuple = ()) -> dict[tuple, tuple]:
    """Get a fingerprint of the data, to check whether it is changed.

    Parameters
    ----------
    data : Any
        The data.
    path : tuple, optional
        The keys (or indices) leading to ``data`` (default ()).

    Returns
    -------
    dict
        For each path, the value (to check it is not replaced) and its
        checksums (to check it is not changed in place).

    """
    out = {path: (data, _checksums(data))}
    if isinstance(data, dict):
        items = data.items()
    elif isinstance(data, list | tuple):
        items = enumerate(data)
    else:
        items = ()
    for key, value in items:
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
    if isinstance(new_value, SpatialImage):
        # The affine must be the same
        if old_sums[0] != new_sums[0]:
            return True
        for old_data, new_data, data in zip(
            old_sums[1:], new_sums[1:], _image_data(new_value), strict=True
        ):
            if new_data is None:
                # Not in memory (or no longer cached)
                continue
            if old_data is not None and old_data[1] == new_data[1]:
                # Same dtype: the data in memory must be the same
                if old_data != new_data:
                    return True
            else:
                # The data was cached during the computation, possibly with
                # another dtype: compare it with the data read from the file
                expected = np.asanyarray(new_value.dataobj, dtype=data.dtype)
                if not np.array_equal(data, expected, equal_nan=True):
                    return True
        return False
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
