"""Provide implementation for read-and-transform function."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL


from typing import TYPE_CHECKING, Dict, Optional, Tuple, Type

import pandas as pd

from ..utils import logger, raise_error, warn_with_log


if TYPE_CHECKING:
    from junifer.storage import BaseFeatureStorage


def read_transform(
    storage: Type["BaseFeatureStorage"],
    feature_name: str,
    transform: str,
    transform_args: Optional[Tuple] = None,
    transform_kw_args: Optional[Dict] = None,
) -> pd.DataFrame:
    """Read stored feature and transform to specific statistical output.

    Parameters
    ----------
    storage : storage-like
        The storage class, for example, SQLiteFeatureStorage.
    feature_name : str
        Name of the feature to read.
    transform : str
        The kind of transform formatted as ``<package>_<function>``,
        for example, ``bctpy_degrees_und``.
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

    # Read storage
    stored_data = storage.read(feature_name=feature_name)  # type: ignore
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
        except ImportError as err:
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

        # Apply function and store subject-wise
        output_list = []
        logger.debug(
            f"Computing '{package}.{func_str}' for feature {feature_name} ..."
        )
        for subject in range(stored_data["data"].shape[2]):
            output = func(
                stored_data["data"][:, :, subject],
                *transform_args,
                **transform_kw_args,
            )
            output_list.append(output)

        # Create dataframe for index
        idx_df = pd.DataFrame(data=stored_data["element"])
        # Create multiindex from dataframe
        logger.debug(
            f"Generating pandas.MultiIndex for feature {feature_name} ..."
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
