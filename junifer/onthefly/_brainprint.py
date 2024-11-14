"""Provide onthefly functions for BrainPrint post-analysis."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Optional

import numpy as np
import pandas as pd

from ..typing import StorageLike
from ..utils import raise_error


__all__ = ["normalize", "reweight"]


def normalize(
    storage: StorageLike,
    features: dict[str, dict[str, Optional[str]]],
    kind: str,
) -> pd.DataFrame:
    """Read stored brainprint data and normalize either surfaces or volumes.

    Parameters
    ----------
    storage : storage-like
        The storage class, for example, :class:`.HDF5FeatureStorage`.
    features : dict, optional
        The feature names or MD5 hashes to read as dict.
        The dict should have the keys:

        * ``"areas"`` (if ``kind="surface"``)
        * ``"volumes"`` (if ``kind="volume"``)
        * ``"eigenvalues"``

        and the corresponding value for each of the keys is again
        a dict with the keys:

        * ``"feature_name"`` : str or None
        * ``"feature_md5"`` : str or None

        Either one of ``"feature_name"`` or ``"feature_md5"`` needs to be
        not None for each first-level key, but both keys are mandatory.

    kind : {"surface", "volume"}
        The kind of normalization.

    Returns
    -------
    pandas.DataFrame
        The transformed feature as a ``pandas.DataFrame``.

    Raises
    ------
    ValueError
        If ``kind`` is invalid.

    """
    # Read storage
    data_dict = {}
    for k, v in features.items():
        data_dict[k] = storage.read_df(**v)  # type: ignore

    # Check and normalize
    valid_kind = ["surface", "volume"]
    normalized_df = None
    if kind == "surface":
        eigenvalues_df = data_dict["eigenvalues"]
        areas_df = data_dict["areas"]
        normalized_df = eigenvalues_df.combine(
            areas_df, lambda left, right: left * right
        )
    elif kind == "volume":
        eigenvalues_df = data_dict["eigenvalues"]
        volumes_df = data_dict["volumes"]
        normalized_df = eigenvalues_df.combine(
            volumes_df, lambda left, right: left * right ** np.divide(2.0, 3.0)
        )
    else:
        raise_error(
            "Invalid value for `kind`, should be one of: " f"{valid_kind}"
        )

    return normalized_df


def reweight(
    storage: StorageLike,
    feature_name: Optional[str] = None,
    feature_md5: Optional[str] = None,
) -> pd.DataFrame:
    """Read stored brainprint data and reweight eigenvalues.

    Parameters
    ----------
    storage : storage-like
        The storage class, for example, :class:`.HDF5FeatureStorage`.
    feature_name : str, optional
        Name of the feature to read (default None).
    feature_md5 : str, optional
        MD5 hash of the feature to read (default None).

    Returns
    -------
    pandas.DataFrame
        The transformed feature as a ``pandas.DataFrame``.

    """
    # Read storage
    eigenvalues_df = storage.read_df(
        feature_name=feature_name, feature_md5=feature_md5
    )  # type: ignore

    # Create data for operation
    exploded_count_idx_df = (
        eigenvalues_df.reset_index("eigenvalue")
        .index.value_counts()
        .apply(lambda x: np.arange(1, x + 1).astype(float))
        .to_frame()
        .explode("count")
    )
    idx_data = (
        pd.concat(
            [exploded_count_idx_df] * len(eigenvalues_df.columns), axis=1
        )
        .reset_index()
        .drop("subject", axis=1, inplace=False)
        .to_numpy()
    )
    idx_df = pd.DataFrame(
        data=idx_data,
        index=eigenvalues_df.index,
        columns=eigenvalues_df.columns,
    )

    # Combine
    return eigenvalues_df.combine(idx_df, lambda left, right: left / right)
