"""Provide functions for statistics."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Any, Callable, Dict, Optional

import numpy as np
from scipy.stats import trim_mean
from scipy.stats.mstats import winsorize

from .utils import logger, raise_error


def get_aggfunc_by_name(
    name: str, func_params: Optional[Dict[str, Any]] = None
) -> Callable:
    """Get an aggregation function by its name.

    Parameters
    ----------
    name : str
        Name to identify the function. Currently supported names and
        corresponding functions are:

        * ``winsorized_mean`` -> :func:`scipy.stats.mstats.winsorize`
        * ``mean`` -> :func:`numpy.mean`
        * ``std`` -> :func:`numpy.std`
        * ``trim_mean`` -> :func:`scipy.stats.trim_mean`

    func_params : dict, optional
        Parameters to pass to the function.
        E.g. for ``winsorized_mean``: ``func_params = {'limits': [0.1, 0.1]}``
        (default None).

    Returns
    -------
    function
        Respective function with ``func_params`` parameter set.
    """
    from functools import partial  # local import to avoid sphinx error

    # check validity of names
    _valid_func_names = {"winsorized_mean", "mean", "std", "trim_mean"}
    if func_params is None:
        func_params = {}
    # apply functions
    if name == "winsorized_mean":
        # check validity of func_params
        limits = func_params.get("limits")
        if limits is None or not isinstance(limits, list):
            raise_error(
                "func_params must contain a list of limits for "
                "winsorized_mean",
                ValueError,
            )
        if len(limits) != 2:
            raise_error(
                "func_params must contain a list of two limits for "
                "winsorized_mean",
                ValueError,
            )
        if any((lim < 0.0 or lim > 1) for lim in limits):
            raise_error(
                "Limits for the winsorized mean must be between 0 and 1."
            )
        logger.info(f"Limits for winsorized mean are set to {limits}.")
        # partially interpret func_params
        func = partial(winsorized_mean, **func_params)
    elif name == "mean":
        func = np.mean
    elif name == "std":
        func = np.std
    elif name == "trim_mean":
        func = partial(trim_mean, **func_params)
    else:
        raise_error(
            f"Function {name} unknown. Please provide any of "
            f"{_valid_func_names}"
        )
    return func


def winsorized_mean(
    data: np.ndarray, axis: Optional[int] = None, **win_params
) -> np.ndarray:
    """Compute a winsorized mean by chaining winsorization and mean.

    Parameters
    ----------
    data : numpy.ndarray
        Data to calculate winsorized mean on.
    axis : int, optional
        The axis to calculate winsorized mean on (default None).
    **win_params : dict
        Dictionary containing the keyword arguments for the winsorize function.
        E.g. ``{'limits': [0.1, 0.1]}``.

    Returns
    -------
    numpy.ndarray
        Winsorized mean of the inputted data with the winsorize settings
        applied as specified in ``win_params``.

    See Also
    --------
    scipy.stats.mstats.winsorize :
        The winsorize function used in this function.
    """
    win_dat = winsorize(data, axis=axis, **win_params)
    win_mean = win_dat.mean(axis=axis)

    return win_mean
