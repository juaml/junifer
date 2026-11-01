"""Provide tests for the base model of the pipeline components."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from typing import Any

import pytest
from pydantic import ConfigDict, ValidationError

from junifer.datareader import DefaultDataReader
from junifer.pipeline import (
    PipelineComponentModel,
    PipelineComponentRegistry,
)


class _Component(PipelineComponentModel):
    """A pipeline component."""

    a: int = 1
    b: int = 2

    def model_post_init(self, context: Any) -> None:
        # Not set by the user
        self.b = 3


def _fields_set(obj: PipelineComponentModel) -> list[str]:
    """Get the parameters set stored in the metadata of a component."""
    data = {}
    obj.update_meta(data, step_name="step")
    return data["meta"]["step"]["_fields_set"]


def test_PipelineComponentModel_fields_set() -> None:
    """Test the names of the parameters given are stored."""
    assert _Component(a=4)._fields_set == {"a"}
    assert _Component()._fields_set == set()
    assert _Component.model_validate({"a": 4})._fields_set == {"a"}
    assert _fields_set(_Component(a=4)) == ["a"]
    # Changed by model_post_init, but not given
    assert "b" in _Component(a=4).model_fields_set


def test_PipelineComponentModel_fields_set_not_validated() -> None:
    """Test the parameters set without validating the parameters.

    The parameters set as known by pydantic are used (including the ones set
    by ``model_post_init``, which ``model_construct`` also calls).

    """
    obj = _Component.model_construct(a=4)
    assert obj._fields_set is None
    assert _fields_set(obj) == sorted(obj.model_fields_set)


def test_PipelineComponentModel_config() -> None:
    """Test the validation of the parameters."""
    with pytest.raises(ValidationError, match="Extra inputs"):
        _Component(c=1)

    class _ExtraComponent(_Component):
        """A pipeline component allowing other parameters."""

        model_config = ConfigDict(extra="allow")

    obj = _ExtraComponent(a=4, c=1)
    assert obj._fields_set == {"a", "c"}
    assert _fields_set(obj) == ["a", "c"]


@pytest.mark.parametrize(
    "step", ["datagrabber", "datareader", "preprocessing", "marker"]
)
def test_PipelineComponentModel_builtin_components(step: str) -> None:
    """Test the built-in components are pipeline component models.

    Parameters
    ----------
    step : str
        The parametrized step of the pipeline.

    """
    registry = PipelineComponentRegistry()
    for name in registry.step_components(step):
        if not registry.is_builtin(step=step, name=name):
            continue
        klass = registry.get_class(step=step, name=name)
        assert issubclass(klass, PipelineComponentModel), name


def test_PipelineComponentModel_datareader() -> None:
    """Test the parameters set of the DataReader, without parameters."""
    assert _fields_set(DefaultDataReader()) == []
