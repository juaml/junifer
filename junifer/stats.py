from functools import partial
import numpy as np
from scipy.stats.mstats import winsorize
from scipy.stats import trim_mean
from .utils import logger, raise_error


def get_aggfunc_by_name(name, func_params):
    """
    Helper function to get an aggregation function by its name.

    Parameters
    ----------
    name : str
        Name to identify the function. Currently supported names and
        corresponding functions are:
        'winsorized_mean' -> scipy.stats.mstats.winsorize
        'mean' -> np.mean
        'std' -> np.std
        'trim_mean' -> scipy.stats.trim_mean

    func_params : dict
        Parameters to pass to the function.
        E.g. for 'winsorized_mean': func_params = {'limits': [0.1, 0.1]}

    Returns
    -------
    func : function
        Respective function with `func_params` parameter set.
    """

    # check validity of names
    _valid_func_names = {'winsorized_mean', 'mean', 'std', 'trim_mean'}

    # apply functions
    if name == 'winsorized_mean':
        # check validity of func_params
        limits = func_params.get('limits')
        if all((lim >= 0.0 and lim <= 1) for lim in limits):
            logger.info(f'Limits for winsorized mean are set to {limits}.')
        else:
            raise_error(
                'Limits for the winsorized mean must be between 0 and 1.')
        # partially interpret func_params
        func = partial(winsorized_mean, **func_params)
    elif name == 'mean':
        func = np.mean
    elif name == 'std':
        func = np.std
    elif name == 'trim_mean':
        func = partial(trim_mean, **func_params)
    else:
        raise_error(f'Function {name} unknown. Please provide any of '
                    f'{_valid_func_names}')
    return func


def winsorized_mean(data, axis=None, **win_params):
    """
    Compute a winsorized mean by chaining winsorization and mean.

    Parameters
    ----------
    data : array
        Data to calculate winsorized mean on.
    win_params : dict
        Dictionary containing the keyword arguments for the winsorize function.
        E.g. {'limits': [0.1, 0.1]}

    Returns
    -------
    win_mean : np.ndarray
        Winsorized mean of the inputted data with the winsorize settings
        applied as specified in win_params.
    """

    win_dat = winsorize(data, axis=axis, **win_params)
    win_mean = win_dat.mean(axis=axis)

    return win_mean
