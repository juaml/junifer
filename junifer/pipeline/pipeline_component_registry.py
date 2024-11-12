"""Provide a class for centralized pipeline component registry."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import importlib
from collections.abc import Mapping
from typing import Optional, Union

from ..typing import DataGrabberLike, MarkerLike, PreprocessorLike, StorageLike
from ..utils import logger, raise_error
from ..utils.singleton import Singleton


__all__ = ["PipelineComponentRegistry"]


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
            },
            "marker": {
                "ALFFParcels": "ALFFParcels",
                "ALFFSpheres": "ALFFSpheres",
                "BaseMarker": "BaseMarker",
                "BrainPrint": "BrainPrint",
                "CrossParcellationFC": "CrossParcellationFC",
                "EdgeCentricFCParcels": "EdgeCentricFCParcels",
                "EdgeCentricFCSpheres": "EdgeCentricFCSpheres",
                "FunctionalConnectivityParcels": (
                    "FunctionalConnectivityParcels"
                ),
                "FunctionalConnectivitySpheres": (
                    "FunctionalConnectivitySpheres"
                ),
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

    def _check_valid_step(self, step: str) -> None:
        """Check if ``step`` is valid."""
        if step not in self._steps:
            raise_error(msg=f"Invalid step: {step}", klass=ValueError)

    @property
    def steps(self) -> list[str]:
        """Get valid pipeline steps."""
        return self._steps

    @property
    def components(self) -> Mapping[str, Mapping[str, Union[str, type]]]:
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
        init_params: Optional[dict] = None,
    ) -> Union[DataGrabberLike, PreprocessorLike, MarkerLike, StorageLike]:
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
