"""Provide functions for registry."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import importlib
from typing import TYPE_CHECKING, Dict, List, Optional, Union

from ..utils.logging import logger, raise_error


if TYPE_CHECKING:
    from ..datagrabber import BaseDataGrabber
    from ..storage import BaseFeatureStorage
    from .pipeline_step_mixin import PipelineStepMixin


__all__ = ["register", "get_step_names", "get_class", "build"]


# Define valid steps for operation
_VALID_STEPS: List[str] = [
    "datagrabber",
    "datareader",
    "preprocessing",
    "marker",
    "storage",
]

# Step to sub-package mapping
_STEP_TO_SUBPKG_MAPPINGS = {
    "datagrabber": "datagrabber",
    "datareader": "datareader",
    "preprocessing": "preprocess",
    "marker": "markers",
    "storage": "storage",
}

# Define registry for valid steps
_REGISTRY: Dict[str, Dict[str, Union[str, type]]] = {
    "datagrabber": {
        "HCP1200": "HCP1200",
        "BaseDataGrabber": "BaseDataGrabber",
        "DataladAOMICID1000": "DataladAOMICID1000",
        "DataladAOMICPIOP1": "DataladAOMICPIOP1",
        "DataladAOMICPIOP2": "DataladAOMICPIOP2",
        "DataladDataGrabber": "DataladDataGrabber",
        "DataladHCP1200": "DataladHCP1200",
        "DMCC13Benchmark": "DMCC13Benchmark",
        "MultipleDataGrabber": "MultipleDataGrabber",
        "PatternDataGrabber": "PatternDataGrabber",
        "PatternDataladDataGrabber": "PatternDataladDataGrabber",
    },
    "datareader": {
        "DefaultDataReader": "DefaultDataReader",
    },
    "preprocessing": {
        "BasePreprocessor": "BasePreprocessor",
        "Smoothing": "Smoothing",
        "SpaceWarper": "SpaceWarper",
        "fMRIPrepConfoundRemover": "fMRIPrepConfoundRemover",
    },
    "marker": {
        "ALFFParcels": "ALFFParcels",
        "ALFFSpheres": "ALFFSpheres",
        "BaseMarker": "BaseMarker",
        "BrainPrint": "BrainPrint",
        "CrossParcellationFC": "CrossParcellationFC",
        "EdgeCentricFCParcels": "EdgeCentricFCParcels",
        "EdgeCentricFCSpheres": "EdgeCentricFCSpheres",
        "FunctionalConnectivityParcels": "FunctionalConnectivityParcels",
        "FunctionalConnectivitySpheres": "FunctionalConnectivitySpheres",
        "ParcelAggregation": "ParcelAggregation",
        "ReHoParcels": "ReHoParcels",
        "ReHoSpheres": "ReHoSpheres",
        "RSSETSMarker": "RSSETSMarker",
        "SphereAggregation": "SphereAggregation",
        "TemporalSNRParcels": "TemporalSNRParcels",
        "TemporalSNRSpheres": "TemporalSNRSpheres",
    },
    "storage": {
        "BaseFeatureStorage": "BaseFeatureStorage",
        "HDF5FeatureStorage": "HDF5FeatureStorage",
        "PandasBaseFeatureStorage": "PandasBaseFeatureStorage",
        "SQLiteFeatureStorage": "SQLiteFeatureStorage",
    },
}


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

    Raises
    ------
    ValueError
        If the ``step`` is invalid.

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

    Raises
    ------
    ValueError
        If the ``step`` is invalid.

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

    Raises
    ------
    ValueError
        If the ``step`` or ``name`` is invalid.

    """
    # Verify step
    if step not in _VALID_STEPS:
        raise_error(msg=f"Invalid step: {step}", klass=ValueError)
    # Verify step name
    if name not in _REGISTRY[step]:
        raise_error(msg=f"Invalid name: {name}", klass=ValueError)

    # Check if first-time import, then import it
    if isinstance(_REGISTRY[step][name], str):
        klass = getattr(
            importlib.import_module(
                f"junifer.{_STEP_TO_SUBPKG_MAPPINGS[step]}"
            ),
            name,
        )
    else:
        klass = _REGISTRY[step][name]

    return klass


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
    init_params : dict or None, optional
        Parameters to pass to the base class constructor (default None).

    Returns
    -------
    object
        An instance of the given base class.

    Raises
    ------
    RuntimeError
        If there is a problem creating the instance.
    ValueError
        If the created object with the given name is not an instance of the
        base class.

    """
    # Set default init parameters
    if init_params is None:
        init_params = {}
    # Get class of the registered function
    logger.debug(f"Building {step}/{name}")
    klass = get_class(step=step, name=name)
    logger.debug(f"\tClass: {klass.__name__}")
    logger.debug(f"\tInit params: {init_params}")
    try:
        # Create instance of the class
        object_ = klass(**init_params)
    except (ValueError, TypeError) as e:
        raise_error(
            msg=f"Failed to create {step} ({name}). Error: {e}",
            klass=RuntimeError,
            exception=e,
        )
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
