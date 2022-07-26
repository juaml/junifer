"""Provide functions for registry."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL

from ..utils.logging import raise_error, logger

_valid_steps = [
    'datagrabber', 'datareader', 'preprocessing', 'marker', 'storage']

_registry = {x: {} for x in _valid_steps}


def register(step, name, klass):
    """Register a function to be used in a pipeline step.

    Parameters
    ----------
    step : str
        Name of the step
    name : str
        Name of the function
    klass : class
        Class to be registered
    """
    if step not in _valid_steps:
        raise_error(f'Invalid step: {step}', ValueError)
    logger.info(f'Registering {name} in {step}')
    _registry[step][name] = klass


def get_step_names(step):
    """Get the names of the registered functions for a given step.

    Parameters
    ----------
    step : str
        Name of the step

    Returns
    -------
    list
        List of registered function names
    """
    if step not in _valid_steps:
        raise_error(f'Invalid step: {step}', ValueError)
    return list(_registry[step].keys())


def get(step, name):
    """Get the class of the registered function for a given step.

    Parameters
    ----------
    step : str
        Name of the step
    name : str
        Name of the function

    Returns
    -------
    class
        Registered function class
    """
    if step not in _valid_steps:
        raise_error(f'Invalid step: {step}', ValueError)
    if name not in _registry[step]:
        raise_error(f'Invalid name: {name}', ValueError)
    return _registry[step][name]


def build(step, name, baseclass, init_params=None):
    """Ensure that the given object is an instance of the given class.

    Parameters
    ----------
    step : str
        Name of the step
    name : str
        Name of the function.
    baseclass : class
        Class to be checked against
    init_parms : dict
        Parameters to pass to the class constructor

    Returns
    -------
    object
        Object if it is an instance of the given class, otherwise a
        ValueError is raised

    Raises
    ------
    ValueError
        If the name is not a string or the object is not an instance of the
        baseclass parameter.
    """
    klass = get(step, name)
    if init_params is None:
        init_params = {}
    object = klass(**init_params)
    if not isinstance(object, baseclass):
        raise_error(
            f'Invalid {step} ({object.__class__.__name__}). '
            f'Must inherit from {baseclass.__name__}', ValueError)
    return object
