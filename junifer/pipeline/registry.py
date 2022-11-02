"""Provide functions for registry."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import TYPE_CHECKING, Dict, List, Optional, Union

from ..utils.logging import logger, raise_error


if TYPE_CHECKING:
    from ..datagrabber import BaseDataGrabber
    from ..storage import BaseFeatureStorage
    from .pipeline_step_mixin import PipelineStepMixin


# Define valid steps for operation
_VALID_STEPS: List[str] = [
    "datagrabber",
    "datareader",
    "preprocessing",
    "marker",
    "storage",
]

# Define registry for valid steps
_REGISTRY: Dict[str, Dict[str, type]] = {x: {} for x in _VALID_STEPS}


def register(step: str, name: str, klass: type) -> None:
    """Register a function to be used in a pipeline step.

    Parameters
    ----------
    step : str
        Name of the step.
    name : str
        Name of the function.
    klass : class
        Class to be registered.

    """
    # Verify step
    if step not in _VALID_STEPS:
        raise_error(msg=f"Invalid step: {step}", klass=ValueError)

    logger.info(f"Registering {name} in {step}")
    _REGISTRY[step][name] = klass


def get_step_names(step: str) -> List[str]:
    """Get the names of the registered functions for a given step.

    Parameters
    ----------
    step : str
        Name of the step.

    Returns
    -------
    list
        List of registered function names.

    """
    # Verify step
    if step not in _VALID_STEPS:
        raise_error(msg=f"Invalid step: {step}", klass=ValueError)

    return list(_REGISTRY[step].keys())


def get_class(step: str, name: str) -> type:
    """Get the class of the registered function for a given step.

    Parameters
    ----------
    step : str
        Name of the step.
    name : str
        Name of the function.

    Returns
    -------
    class
        Registered function class.

    """
    # Verify step
    if step not in _VALID_STEPS:
        raise_error(msg=f"Invalid step: {step}", klass=ValueError)
    # Verify step name
    if name not in _REGISTRY[step]:
        raise_error(msg=f"Invalid name: {name}", klass=ValueError)

    return _REGISTRY[step][name]


def build(
    step: str,
    name: str,
    baseclass: type,
    init_params: Optional[Dict] = None,
) -> Union["BaseDataGrabber", "PipelineStepMixin", "BaseFeatureStorage"]:
    """Ensure that the given object is an instance of the given class.

    Parameters
    ----------
    step : str
        Name of the step.
    name : str
        Name of the function.
    baseclass : class
        Class to be checked against.
    init_parms : dict, optional
        Parameters to pass to the base class constructor (default None).

    Returns
    -------
    object
        An instance of the given base class.

    Raises
    ------
    ValueError
        If the created object with the given name is not an instance of the
        base class.

    """
    # Set default init parameters
    if init_params is None:
        init_params = {}
    # Get class of the registered function
    klass = get_class(step=step, name=name)
    # Create instance of the class
    object_ = klass(**init_params)
    # Verify created instance belongs to the base class
    if not isinstance(object_, baseclass):
        raise_error(
            msg=(
                f"Invalid {step} ({object_.__class__.__name__}). "
                f"Must inherit from {baseclass.__name__}"
            ),
            klass=ValueError,
        )
    return object_
