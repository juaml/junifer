"""Provide tests for PipelineComponentRegistry."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import logging
from abc import ABC

import pytest

from junifer.datagrabber.pattern import PatternDataGrabber
from junifer.pipeline.pipeline_component_registry import (
    PipelineComponentRegistry,
)
from junifer.storage import SQLiteFeatureStorage


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
        ("storage", SQLiteFeatureStorage),
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
        ("storage", SQLiteFeatureStorage),
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
    with caplog.at_level(logging.INFO):
        # Register
        PipelineComponentRegistry().deregister(step=step, klass=klass)
        # Check logging message
        assert "De-registering" in caplog.text


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
