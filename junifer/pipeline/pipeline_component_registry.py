"""Provide a class for centralized pipeline component registry."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import importlib
import sys
from collections.abc import Mapping
from pathlib import Path

import structlog

from ..typing import DataGrabberLike, MarkerLike, PreprocessorLike, StorageLike
from ..utils import raise_error
from ..utils.singleton import Singleton


__all__ = ["PipelineComponentRegistry"]

_log = structlog.get_logger("junifer")
logger = _log.bind(pkg="pipeline")

# The modules calling `PipelineComponentRegistry.register` on behalf of
# another module (e.g., the `register_*` decorators)
_REGISTERING_MODULES = {
    __name__,
    "junifer.api.decorators",
}


def _registering_module() -> str | None:
    """Get the module registering a component.

    It is the first module in the call stack that is not one of the modules
    registering components on behalf of another module (e.g., the module
    defining a component with ``@register_marker`` or registering it with
    ``PipelineComponentRegistry().register``), as imported with ``with`` in
    the YAML.

    Returns
    -------
    str or None
        The name of the module (or the path of the file, if loaded from a file
        with ``with`` in the YAML), or None if it cannot be imported (e.g., a
        script).

    """
    frame = sys._getframe(1)
    while (
        frame is not None
        and frame.f_globals.get("__name__") in _REGISTERING_MODULES
    ):
        frame = frame.f_back
    if frame is None:
        return None
    name = frame.f_globals.get("__name__")
    if name is None or name == "__main__":
        return None
    # The files loaded with `with` in the YAML are named by their path in
    # the YAML, so use their absolute path
    file = frame.f_globals.get("__file__")
    if name.endswith(".py") and file is not None:
        return str(Path(file).resolve())
    return name


class PipelineComponentRegistry(metaclass=Singleton):
    """Class for pipeline component registry.

    This class is a singleton and is used for managing pipeline components.
    It serves as a centralized registry for built-in and third-party pipeline
    components like datagrabbers, datareaders, preprocessors, markers and
    storage.

    Attributes
    ----------
    steps : list of str
        Valid pipeline steps.
    components : dict
        Registered components for valid pipeline steps.

    """

    def __init__(self) -> None:
        """Initialize the class."""
        # Valid steps for operation
        self._steps = [
            "datagrabber",
            "datareader",
            "preprocessing",
            "marker",
            "storage",
        ]
        # Step to sub-package mapping
        self._step_to_subpkg_mappings = {
            "datagrabber": "datagrabber",
            "datareader": "datareader",
            "preprocessing": "preprocess",
            "marker": "markers",
            "storage": "storage",
        }
        # Component registry for valid steps
        self._components = {
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
                "TemporalSlicer": "TemporalSlicer",
                "TemporalFilter": "TemporalFilter",
            },
            "marker": {
                "ALFFMaps": "ALFFMaps",
                "ALFFParcels": "ALFFParcels",
                "ALFFSpheres": "ALFFSpheres",
                "BaseMarker": "BaseMarker",
                "BrainPrint": "BrainPrint",
                "CrossParcellationFC": "CrossParcellationFC",
                "EdgeCentricFCMaps": "EdgeCentricFCMaps",
                "EdgeCentricFCParcels": "EdgeCentricFCParcels",
                "EdgeCentricFCSpheres": "EdgeCentricFCSpheres",
                "FunctionalConnectivityMaps": "FunctionalConnectivityMaps",
                "FunctionalConnectivityParcels": (
                    "FunctionalConnectivityParcels"
                ),
                "FunctionalConnectivitySpheres": (
                    "FunctionalConnectivitySpheres"
                ),
                "MapsAggregation": "MapsAggregation",
                "ParcelAggregation": "ParcelAggregation",
                "ReHoMaps": "ReHoMaps",
                "ReHoParcels": "ReHoParcels",
                "ReHoSpheres": "ReHoSpheres",
                "RSSETSMarker": "RSSETSMarker",
                "SphereAggregation": "SphereAggregation",
                "TemporalSNRMaps": "TemporalSNRMaps",
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
        # The built-in components, imported when first used
        self._builtins = {
            step: set(components)
            for step, components in self._components.items()
        }
        # The modules that registered the other components
        self._registering_modules: dict[type, str | None] = {}

    def _check_valid_step(self, step: str) -> None:
        """Check if ``step`` is valid."""
        if step not in self._steps:
            raise_error(msg=f"Invalid step: {step}", klass=ValueError)

    @property
    def steps(self) -> list[str]:
        """Get valid pipeline steps."""
        return self._steps

    @property
    def components(self) -> Mapping[str, Mapping[str, str | type]]:
        """Get registered components for valid pipeline steps."""
        return self._components

    def register(self, step: str, klass: type) -> None:
        """Register ``klass`` under ``step``.

        Parameters
        ----------
        step : str
            Name of the pipeline step. For valid steps, check :meth:`.steps`.
        klass : class
            Class to be registered.

        Raises
        ------
        ValueError
            If the ``step`` is invalid.

        """
        # Verify step
        self._check_valid_step(step)
        # Log and register
        name = klass.__name__
        logger.info(f"Registering {name} in {step}")
        self._components[step][name] = klass
        self._registering_modules[klass] = _registering_module()

    def deregister(self, step: str, klass: type) -> None:
        """De-register ``klass`` under ``step``.

        Parameters
        ----------
        step : str
            Name of the pipeline step. For valid steps, check :meth:`.steps`.
        klass : class
            Class to be de-registered.

        Raises
        ------
        ValueError
            If the ``step`` is invalid.

        """
        # Verify step
        self._check_valid_step(step)
        # Log and de-register
        name = klass.__name__
        logger.info(f"De-registering {name} in {step}")
        _ = self._components[step].pop(name)

    def is_builtin(self, step: str, name: str) -> bool:
        """Check whether a component is built-in.

        The built-in components are available without loading them with
        ``with`` in the YAML.

        Parameters
        ----------
        step : str
            Name of the pipeline step. For valid steps, check :meth:`.steps`.
        name : str
            Name of the component.

        Returns
        -------
        bool
            Whether the component is built-in.

        Raises
        ------
        ValueError
            If the ``step`` is invalid.

        """
        self._check_valid_step(step)
        return name in self._builtins[step]

    def get_registering_module(self, klass: type) -> str | None:
        """Get the module that registered a component.

        It is the module to load with ``with`` in the YAML to use the
        component.

        Parameters
        ----------
        klass : class
            The class of the component.

        Returns
        -------
        str or None
            The name of the module (or the path of the file, if loaded from a
            file with ``with`` in the YAML), or None if the component is
            built-in (it does not need to be loaded) or the module is unknown.

        """
        if klass.__module__.startswith("junifer.") and any(
            klass.__name__ in builtins for builtins in self._builtins.values()
        ):
            return None
        return self._registering_modules.get(klass)

    def step_components(self, step: str) -> list[str]:
        """Get registered components for ``step``.

        Parameters
        ----------
        step : str
            Name of the pipeline step.

        Returns
        -------
        list of str
            List of registered component classes.

        Raises
        ------
        ValueError
            If the ``step`` is invalid.

        """
        # Verify step
        self._check_valid_step(step)

        return list(self._components[step].keys())

    def get_class(self, step: str, name: str) -> type:
        """Get the class registered under ``name`` for ``step``.

        Parameters
        ----------
        step : str
            Name of the pipeline step.
        name : str
            Name of the component.

        Returns
        -------
        class
            Registered class.

        Raises
        ------
        ValueError
            If the ``step`` or ``name`` is invalid.

        """
        # Verify step
        self._check_valid_step(step)
        # Verify step name
        if name not in self._components[step]:
            raise_error(msg=f"Invalid name: {name}", klass=ValueError)

        # Check if first-time import, then import it
        if isinstance(self._components[step][name], str):
            klass = getattr(
                importlib.import_module(
                    f"junifer.{self._step_to_subpkg_mappings[step]}"
                ),
                name,
            )
        else:
            klass = self._components[step][name]

        return klass

    def build_component_instance(
        self,
        step: str,
        name: str,
        baseclass: type,
        init_params: dict | None = None,
    ) -> DataGrabberLike | PreprocessorLike | MarkerLike | StorageLike:
        """Build an instance of class registered as ``name``.

        Parameters
        ----------
        step : str
            Name of the pipeline step.
        name : str
            Name of the component.
        baseclass : class
            Base class to be checked against.
        init_params : dict or None, optional
            Parameters to pass to the class constructor (default None).

        Returns
        -------
        object
            An instance of the class registered as ``name`` under ``step``.

        Raises
        ------
        RuntimeError
            If there is a problem creating the instance.
        ValueError
            If the created object with the given name is not a subclass of the
            base class ``baseclass``.

        """
        # Set default init parameters
        if init_params is None:
            init_params = {}
        # Get registered class
        logger.debug(f"Building {step}/{name}")
        klass = self.get_class(step=step, name=name)
        logger.debug(f"\tClass: {klass.__name__}")
        logger.debug(f"\tInit params: {init_params}")
        try:
            # Create instance of the class
            if step == "datagrabber" and name == "MultipleDataGrabber":
                dgs = []
                for d in init_params["datagrabbers"]:
                    k = d.pop("kind")
                    dg_klass = self.get_class(step=step, name=k)
                    dg_obj = dg_klass(**d)
                    dgs.append(dg_obj)
                object_ = klass(datagrabbers=dgs)
            else:
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
