"""Provide tests for pipeline mixin."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Dict, List

import pytest

from junifer.pipeline.pipeline_step_mixin import PipelineStepMixin


def test_PipelineStepMixin() -> None:
    """Test PipelineStepMixin."""
    mixin = PipelineStepMixin()
    with pytest.raises(NotImplementedError):
        mixin.validate_input([])
    with pytest.raises(NotImplementedError):
        mixin.get_output_type("")
    with pytest.raises(NotImplementedError):
        mixin.fit_transform({})


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
