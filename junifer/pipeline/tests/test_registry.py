"""Provide tests for registry."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL
import logging
from abc import ABC
from typing import Type

import pytest

from junifer.datagrabber import PatternDataGrabber
from junifer.pipeline.registry import (
    build,
    get_class,
    get_step_names,
    register,
)
from junifer.storage import SQLiteFeatureStorage


def test_register_invalid_step():
    """Test register invalid step name."""
    with pytest.raises(ValueError, match="Invalid step:"):
        register(step="foo", name="bar", klass=str)


# TODO: improve parametrization
@pytest.mark.parametrize(
    "step, name, klass",
    [
        ("datagrabber", "pattern-dg", PatternDataGrabber),
        ("storage", "sqlite-storage", SQLiteFeatureStorage),
    ],
)
def test_register(
    caplog: pytest.LogCaptureFixture, step: str, name: str, klass: Type
) -> None:
    """Test register.

    Parameters
    ----------
    caplog : pytest.LogCaptureFixture
        A pytest fixture to capture logging.
    step : str
        The parametrized name of the step.
    name : str
        The parametrized name of the function.
    klass : str
        The parametrized name of the base class.

    """
    with caplog.at_level(logging.INFO):
        # Register
        register(step=step, name=name, klass=klass)
        # Check logging message
        assert "Registering" in caplog.text


def test_get_step_names_invalid_step() -> None:
    """Test get step name invalid step name."""
    with pytest.raises(ValueError, match="Invalid step:"):
        get_step_names(step="foo")


def test_get_step_names_absent() -> None:
    """Test get step names for absent name."""
    # Get step names for datagrabber
    datagrabbers = get_step_names(step="datagrabber")
    # Check for datagrabber step name
    assert "bar" not in datagrabbers


def test_get_step_names() -> None:
    """Test get step names."""
    # Register datagrabber
    register(step="datagrabber", name="bar", klass=str)
    # Get step names for datagrabber
    datagrabbers = get_step_names(step="datagrabber")
    # Check for datagrabber step name
    assert "bar" in datagrabbers


def test_get_class_invalid_step() -> None:
    """Test get class invalid step name."""
    with pytest.raises(ValueError, match="Invalid step:"):
        get_class(step="foo", name="bar")


def test_get_class_invalid_name() -> None:
    """Test get class invalid function name."""
    with pytest.raises(ValueError, match="Invalid name:"):
        get_class(step="datagrabber", name="foo")


# TODO: enable parametrization
def test_get_class():
    """Test get class."""
    # Register datagrabber
    register(step="datagrabber", name="bar", klass=str)
    # Get class
    obj = get_class(step="datagrabber", name="bar")
    assert obj == str


# TODO: possible parametrization?
def test_build():
    """Test building objects from names."""
    import numpy as np

    # Define abstract base class
    class SuperClass(ABC):
        pass

    # Define concrete class
    class ConcreteClass(SuperClass):
        def __init__(self, value=1):
            self.value = value

    # Register
    register(step="datagrabber", name="concrete", klass=ConcreteClass)

    # Build
    obj = build(step="datagrabber", name="concrete", baseclass=SuperClass)
    assert isinstance(obj, ConcreteClass)
    assert obj.value == 1

    # Build
    obj = build(
        step="datagrabber",
        name="concrete",
        baseclass=SuperClass,
        init_params={"value": 2},
    )
    assert isinstance(obj, ConcreteClass)
    assert obj.value == 2

    # Check error
    with pytest.raises(ValueError, match="Must inherit"):
        build(step="datagrabber", name="concrete", baseclass=np.ndarray)
