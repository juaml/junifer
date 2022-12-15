"""Provide tests for pipeline mixin."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import warnings
from typing import Dict, List

import pytest

from junifer.pipeline.pipeline_step_mixin import PipelineStepMixin
from junifer.pipeline.utils import _check_afni


def test_PipelineStepMixin() -> None:
    """Test PipelineStepMixin."""
    mixin = PipelineStepMixin()
    with pytest.raises(NotImplementedError):
        mixin.validate_input([])
    with pytest.raises(NotImplementedError):
        mixin.get_output_type("")
    with pytest.raises(NotImplementedError):
        mixin._fit_transform({})


def test_pipeline_step_mixin_validate_correct_dependencies() -> None:
    """Test validate with correct dependencies."""

    class CorrectMixer(PipelineStepMixin):
        """Test class for validation."""

        _DEPENDENCIES = {"setuptools"}

        def validate_input(self, input: List[str]) -> None:
            print(input)

        def get_output_type(self, input_type: str) -> str:
            return input_type

        def fit_transform(self, input: Dict[str, Dict]) -> Dict[str, Dict]:
            return {"input": input}

    mixer = CorrectMixer()
    mixer.validate([])


def test_pipeline_step_mixin_validate_incorrect_dependencies() -> None:
    """Test validate with incorrect dependencies."""

    class IncorrectMixer(PipelineStepMixin):
        """Test class for validation."""

        _DEPENDENCIES = {"foobar"}

        def validate_input(self, input: List[str]) -> None:
            print(input)

        def get_output_type(self, input_type: str) -> str:
            return input_type

        def fit_transform(self, input: Dict[str, Dict]) -> Dict[str, Dict]:
            return {"input": input}

    mixer = IncorrectMixer()
    with pytest.raises(ImportError, match="not installed"):
        mixer.validate([])


@pytest.mark.skipif(
    _check_afni() is False, reason="requires afni to be in PATH"
)
def test_pipeline_step_mixin_validate_correct_ext_dependencies() -> None:
    """Test validate with correct external dependencies."""

    class CorrectMixer(PipelineStepMixin):
        """Test class for validation."""

        _EXT_DEPENDENCIES = [{"name": "afni", "optional": False}]

        def validate_input(self, input: List[str]) -> None:
            print(input)

        def get_output_type(self, input_type: str) -> str:
            return input_type

        def fit_transform(self, input: Dict[str, Dict]) -> Dict[str, Dict]:
            return {"input": input}

    mixer = CorrectMixer()
    mixer.validate([])


@pytest.mark.skipif(
    _check_afni() is False, reason="requires afni to be in PATH"
)
def test_pipeline_step_mixin_validate_ext_deps_correct_commands() -> None:
    """Test validate with correct external dependencies' correct commands."""

    class CorrectMixer(PipelineStepMixin):
        """Test class for validation."""

        _EXT_DEPENDENCIES = [
            {"name": "afni", "optional": False, "commands": ["3dReHo"]}
        ]

        def validate_input(self, input: List[str]) -> None:
            print(input)

        def get_output_type(self, input_type: str) -> str:
            return input_type

        def fit_transform(self, input: Dict[str, Dict]) -> Dict[str, Dict]:
            return {"input": input}

    mixer = CorrectMixer()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        mixer.validate([])


@pytest.mark.skipif(
    _check_afni() is False, reason="requires afni to be in PATH"
)
def test_pipeline_step_mixin_validate_ext_deps_incorrect_commands() -> None:
    """Test validate with correct external dependencies' incorrect commands."""

    class CorrectMixer(PipelineStepMixin):
        """Test class for validation."""

        _EXT_DEPENDENCIES = [
            {"name": "afni", "optional": False, "commands": ["3d"]}
        ]

        def validate_input(self, input: List[str]) -> None:
            print(input)

        def get_output_type(self, input_type: str) -> str:
            return input_type

        def fit_transform(self, input: Dict[str, Dict]) -> Dict[str, Dict]:
            return {"input": input}

    mixer = CorrectMixer()
    with pytest.warns(RuntimeWarning, match="AFNI is installed"):
        mixer.validate([])


def test_pipeline_step_mixin_validate_incorrect_ext_dependencies() -> None:
    """Test validate with incorrect external dependencies."""

    class IncorrectMixer(PipelineStepMixin):
        """Test class for validation."""

        _EXT_DEPENDENCIES = [{"name": "foobar", "optional": True}]

        def validate_input(self, input: List[str]) -> None:
            print(input)

        def get_output_type(self, input_type: str) -> str:
            return input_type

        def fit_transform(self, input: Dict[str, Dict]) -> Dict[str, Dict]:
            return {"input": input}

    mixer = IncorrectMixer()
    with pytest.raises(ValueError, match="too adventurous"):
        mixer.validate([])
