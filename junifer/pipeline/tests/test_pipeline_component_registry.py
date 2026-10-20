"""Provide tests for PipelineComponentRegistry."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import importlib
import logging
import pkgutil
from abc import ABC
from pathlib import Path

import pytest

import junifer
from junifer.datagrabber.pattern import PatternDataGrabber
from junifer.pipeline.pipeline_component_registry import (
    PipelineComponentRegistry,
)
from junifer.storage import HDF5FeatureStorage


def test_pipeline_component_registry_singleton() -> None:
    """Test that PipelineComponentRegistry is a singleton."""
    registry_1 = PipelineComponentRegistry()
    registry_2 = PipelineComponentRegistry()
    assert id(registry_1) == id(registry_2)


def test_pipeline_component_registry_register_invalid_step():
    """Test invalid step name during component registration."""
    with pytest.raises(ValueError, match="Invalid step:"):
        PipelineComponentRegistry().register(step="foo", klass=str)


def test_pipeline_component_registry_steps():
    """Test steps for PipelineComponentRegistry."""
    assert set(PipelineComponentRegistry().steps) == {
        "datagrabber",
        "datareader",
        "preprocessing",
        "marker",
        "storage",
    }


def test_pipeline_component_registry_components():
    """Test components for PipelineComponentRegistry."""
    assert set(PipelineComponentRegistry().steps) == {
        "datagrabber",
        "datareader",
        "preprocessing",
        "marker",
        "storage",
    }


@pytest.mark.parametrize(
    "step, klass",
    [
        ("datagrabber", PatternDataGrabber),
        ("storage", HDF5FeatureStorage),
    ],
)
def test_pipeline_component_registry_register(
    caplog: pytest.LogCaptureFixture, step: str, klass: type
) -> None:
    """Test register for PipelineComponentRegistry.

    Parameters
    ----------
    caplog : pytest.LogCaptureFixture
        The pytest.LogCaptureFixture object.
    step : str
        The parametrized name of the step.
    klass : str
        The parametrized name of the class.

    """
    with caplog.at_level(logging.INFO):
        # Register
        PipelineComponentRegistry().register(step=step, klass=klass)
        # Check logging message
        assert "Registering" in caplog.text


@pytest.mark.parametrize(
    "step, klass",
    [
        ("datagrabber", PatternDataGrabber),
        ("storage", HDF5FeatureStorage),
    ],
)
def test_pipeline_component_registry_deregister(
    caplog: pytest.LogCaptureFixture, step: str, klass: type
) -> None:
    """Test de-register for PipelineComponentRegistry.

    Parameters
    ----------
    caplog : pytest.LogCaptureFixture
        The pytest.LogCaptureFixture object.
    step : str
        The parametrized name of the step.
    klass : str
        The parametrized name of the class.

    """
    registry = PipelineComponentRegistry()
    try:
        with caplog.at_level(logging.INFO):
            registry.deregister(step=step, klass=klass)
            # Check logging message
            assert "De-registering" in caplog.text
        assert klass.__name__ not in registry.step_components(step)
    finally:
        # Register again, as the registry is shared by all the tests
        registry.register(step=step, klass=klass)


def test_pipeline_component_registry_step_components() -> None:
    """Test step components for PipelineComponentRegistry."""
    # Check absent name
    assert "fizz" not in PipelineComponentRegistry().step_components(
        step="datagrabber"
    )

    # Create new class
    class fizz(str):
        pass

    # Register datagrabber
    PipelineComponentRegistry().register(step="datagrabber", klass=fizz)
    # Check registered component
    assert "fizz" in PipelineComponentRegistry().step_components(
        step="datagrabber"
    )


def test_pipeline_component_registry_get_class_invalid_name() -> None:
    """Test get class invalid name for PipelineComponentRegistry."""
    with pytest.raises(ValueError, match="Invalid name:"):
        PipelineComponentRegistry().get_class(step="datagrabber", name="foo")


def test_pipeline_component_registry_get_class():
    """Test get class for PipelineComponentRegistry."""

    # Create new class
    class bar(str):
        pass

    # Register datagrabber
    PipelineComponentRegistry().register(step="datagrabber", klass=bar)
    # Get class
    obj = PipelineComponentRegistry().get_class(step="datagrabber", name="bar")
    assert isinstance(obj, type(bar))


def test_pipeline_component_registry_get_class_builtin() -> None:
    """Test get class for the built-in components of the registry."""
    # A new registry, with the built-in components not imported yet (the
    # singleton might have imported some of them)
    registry = object.__new__(PipelineComponentRegistry)
    registry.__init__()
    for step in registry.steps:
        for name in registry.step_components(step=step):
            assert isinstance(registry.components[step][name], str)
            klass = registry.get_class(step=step, name=name)
            assert klass.__name__ == name
    # Import all the components of the sub-packages of the steps, which
    # registers them, and check that they are all built-in components, except
    # the ones with optional dependencies, which are registered by importing
    # their sub-package (e.g., with ``with:`` in the YAML)
    optional = ("junifer.markers.complexity",)
    for module in pkgutil.walk_packages(junifer.__path__, "junifer."):
        if ".tests" in module.name:
            continue
        try:
            importlib.import_module(module.name)
        except ImportError:
            # Only if the optional dependencies are not installed
            assert module.name.startswith(optional)
    for step, subpkg in registry._step_to_subpkg_mappings.items():
        for name, klass in (
            PipelineComponentRegistry().components[step].items()
        ):
            if isinstance(klass, str):
                continue
            if klass.__module__.startswith(optional):
                assert name not in registry.components[step]
            elif klass.__module__.startswith(f"junifer.{subpkg}."):
                assert name in registry.components[step]


def test_pipeline_component_registry_build():
    """Test component instance building for PipelineComponentRegistry."""
    import numpy as np

    # Define abstract base class
    class SuperClass(ABC):
        pass

    # Define concrete class
    class ConcreteClass(SuperClass):
        def __init__(self, value=1):
            self.value = value

    # Register
    PipelineComponentRegistry().register(
        step="datagrabber", klass=ConcreteClass
    )

    # Build
    obj = PipelineComponentRegistry().build_component_instance(
        step="datagrabber", name="ConcreteClass", baseclass=SuperClass
    )
    assert isinstance(obj, ConcreteClass)
    assert obj.value == 1

    # Build
    obj = PipelineComponentRegistry().build_component_instance(
        step="datagrabber",
        name="ConcreteClass",
        baseclass=SuperClass,
        init_params={"value": 2},
    )
    assert isinstance(obj, ConcreteClass)
    assert obj.value == 2

    # Check error
    with pytest.raises(ValueError, match="Must inherit"):
        PipelineComponentRegistry().build_component_instance(
            step="datagrabber", name="ConcreteClass", baseclass=np.ndarray
        )

    # Check error
    with pytest.raises(RuntimeError, match="Failed to create"):
        PipelineComponentRegistry().build_component_instance(
            step="datagrabber",
            name="ConcreteClass",
            baseclass=SuperClass,
            init_params={"wrong": 2},
        )


def test_pipeline_component_registry_is_builtin() -> None:
    """Test checking whether components are built-in."""
    registry = PipelineComponentRegistry()
    assert registry.is_builtin(step="marker", name="ParcelAggregation")
    assert registry.is_builtin(step="datagrabber", name="HCP1200")
    assert not registry.is_builtin(
        step="datagrabber", name="PartlyCloudyTestingDataGrabber"
    )
    assert not registry.is_builtin(step="marker", name="HurstExponent")
    with pytest.raises(ValueError, match="Invalid step"):
        registry.is_builtin(step="foo", name="ParcelAggregation")


def test_pipeline_component_registry_get_registering_module(
    tmp_path: Path,
) -> None:
    """Test getting the module that registered a component.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    from junifer.api import parse_yaml
    from junifer.api.decorators import register_marker
    from junifer.markers import ParcelAggregation
    from junifer.testing.datagrabbers import PartlyCloudyTestingDataGrabber

    registry = PipelineComponentRegistry()
    # Built-in
    assert registry.get_registering_module(ParcelAggregation) is None
    # Registered by another module, imported with `with`
    importlib.import_module("junifer.testing.registry")
    assert (
        registry.get_registering_module(PartlyCloudyTestingDataGrabber)
        == "junifer.testing.registry"
    )

    # Registered by this module, with the decorator
    @register_marker
    class MyParcelAggregation(ParcelAggregation):
        """Parcel aggregation registered in the test."""

    # Registered by a file loaded with `with`
    (tmp_path / "my_marker.py").write_text(
        "from junifer.api.decorators import register_marker\n"
        "from junifer.markers import ParcelAggregation\n\n\n"
        "@register_marker\n"
        "class MyFileParcelAggregation(ParcelAggregation):\n"
        '    """Parcel aggregation registered in a file."""\n'
    )
    (tmp_path / "config.yaml").write_text("with: my_marker.py\n")
    parse_yaml(tmp_path / "config.yaml")
    file_marker = registry.get_class(
        step="marker", name="MyFileParcelAggregation"
    )
    try:
        assert registry.get_registering_module(MyParcelAggregation) == (
            __name__
        )
        assert registry.get_registering_module(file_marker) == str(
            (tmp_path / "my_marker.py").resolve()
        )
        # Not registered
        assert registry.get_registering_module(type("Foo", (), {})) is None
    finally:
        registry.deregister(step="marker", klass=MyParcelAggregation)
        registry.deregister(step="marker", klass=file_marker)
