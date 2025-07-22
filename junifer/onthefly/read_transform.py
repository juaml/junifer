"""Provide implementation for read-and-transform function."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Optional

import numpy as np
import pandas as pd

from ..typing import StorageLike
from ..utils import logger, raise_error, warn_with_log


__all__ = ["read_transform"]


def read_transform(
    storage: StorageLike,
    transform: str,
    feature_name: Optional[str] = None,
    feature_md5: Optional[str] = None,
    nan_policy: Optional[str] = "bypass",
    transform_args: Optional[tuple] = None,
    transform_kw_args: Optional[dict] = None,
) -> pd.DataFrame:
    """Read stored feature and transform to specific statistical output.

    Parameters
    ----------
    storage : storage-like
        The storage class, for example, SQLiteFeatureStorage.
    transform : str
        The kind of transform formatted as ``<package>_<function>``,
        for example, ``bctpy_degrees_und``.
    feature_name : str, optional
        Name of the feature to read (default None).
    feature_md5 : str, optional
        MD5 hash of the feature to read (default None).
    nan_policy : str, optional
        The policy to handle NaN values (default "ignore").
        Options are:

        * "bypass": Do nothing and pass NaN values to the transform function.
        * "drop_element": Drop (skip) elements with NaN values.
        * "drop_rows": Drop (skip) rows with NaN values.
        * "drop_columns": Drop (skip) columns with NaN values.
        * "drop_symmetric": Drop (skip) symmetric pairs with NaN values.

    transform_args : tuple, optional
        The positional arguments for the callable of ``transform``
        (default None).
    transform_kw_args : dict, optional
        The keyword arguments for the callable of ``transform``
        (default None).

    Returns
    -------
    pandas.DataFrame
        The transformed feature as a dataframe.

    Raises
    ------
    ValueError
        If ``nan_policy`` is invalid or
        if *package* is invalid.
    RuntimeError
        If *package* is ``bctpy`` and stored data kind is not ``matrix``.
    ImportError
        If ``bctpy`` cannot be imported.
    AttributeError
        If *function* to be invoked in invalid.

    Notes
    -----
    This function has been only tested for:

    * ``bct.degrees_und``
    * ``bct.strengths_und``
    * ``bct.clustering_coef_wu``
    * ``bct.eigenvector_centrality_und``

    Using other functions may fail and require tweaking.

    """
    # Set default values for args and kwargs
    transform_args = transform_args or ()
    transform_kw_args = transform_kw_args or {}

    if nan_policy not in [
        "bypass",
        "drop_element",
        "drop_rows",
        "drop_columns",
        "drop_symmetric",
    ]:
        raise_error(
            f"Unknown nan_policy: {nan_policy}",
            klass=ValueError,
        )

    # Read storage
    stored_data = storage.read(
        feature_name=feature_name, feature_md5=feature_md5
    )  # type: ignore
    # Retrieve package and function
    package, func_str = transform.split("_", 1)
    # Condition for package
    if package == "bctpy":
        # Check that "matrix" is the feature data kind
        if stored_data["kind"] != "matrix":
            raise_error(
                msg=(
                    f"'{stored_data['kind']}' is not valid data kind for "
                    f"'{package}'"
                ),
                klass=RuntimeError,
            )

        # Check bctpy import
        try:
            import bct
        except ImportError as err:  # pragma: no cover
            raise_error(msg=str(err), klass=ImportError)

        # Warning about function usage
        if func_str not in [
            "degrees_und",
            "strengths_und",
            "clustering_coef_wu",
            "eigenvector_centrality_und",
        ]:
            warn_with_log(
                f"You are about to use '{package}.{func_str}' which has not "
                "been tested to run. In case it fails, you will need to tweak"
                " the code yourself."
            )

        # Retrieve callable object
        try:
            func = getattr(bct, func_str)
        except AttributeError as err:
            raise_error(msg=str(err), klass=AttributeError)

        # Apply function and store element-wise
        output_list = []
        element_list = []
        logger.debug(
            f"Computing '{package}.{func_str}' for feature "
            f"{feature_name or feature_md5} ..."
        )
        for i_element, element in enumerate(stored_data["element"]):
            t_data = stored_data["data"][:, :, i_element]
            has_nan = np.isnan(np.min(t_data))
            if nan_policy == "drop_element" and has_nan:
                logger.debug(
                    f"Skipping element {element} due to NaN values ..."
                )
                continue
            elif nan_policy == "drop_rows" and has_nan:
                logger.debug(
                    f"Skipping rows with NaN values in element {element} ..."
                )
                t_data = t_data[~np.isnan(t_data).any(axis=1)]
            elif nan_policy == "drop_columns" and has_nan:
                logger.debug(
                    f"Skipping columns with NaN values in element {element} "
                    "..."
                )
                t_data = t_data[:, ~np.isnan(t_data).any(axis=0)]
            elif nan_policy == "drop_symmetric":
                logger.debug(
                    f"Skipping pairs of rows/columns with NaN values in "
                    f"element {element}..."
                )
                good_rows = ~np.isnan(t_data).any(axis=1)
                good_columns = ~np.isnan(t_data).any(axis=0)
                good_idx = np.logical_and(good_rows, good_columns)
                t_data = t_data[good_idx][:, good_idx]

            output = func(
                t_data,
                *transform_args,
                **transform_kw_args,
            )
            output_list.append(output)
            element_list.append(element)

        # Create dataframe for index
        idx_df = pd.DataFrame(data=element_list)
        # Create multiindex from dataframe
        logger.debug(
            "Generating pandas.MultiIndex for feature "
            f"{feature_name or feature_md5} ..."
        )
        data_idx = pd.MultiIndex.from_frame(df=idx_df)

        # Create dataframe
        df = pd.DataFrame(
            data=output_list,
            index=data_idx,
            columns=stored_data["row_headers"],
        )
        return df
    else:
        raise_error(f"Unknown package: {package}")
