"""Provide tests for PipelineStepMixin."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import warnings
from typing import ClassVar, Dict, List, Set, Type, Union

import pytest

from junifer.pipeline.pipeline_step_mixin import PipelineStepMixin
from junifer.pipeline.utils import _check_afni


def test_PipelineStepMixin_correct_dependencies() -> None:
    """Test fit-transform with correct dependencies."""

    class CorrectMixer(PipelineStepMixin):
        """Test class for validation."""

        _DEPENDENCIES: ClassVar[Set[str]] = {"math"}

        def validate_input(self, input: List[str]) -> List[str]:
            return input

        def get_output_type(self, input_type: str) -> str:
            return input_type

        def _fit_transform(self, input: Dict[str, Dict]) -> Dict[str, Dict]:
            return {"input": input}

    mixer = CorrectMixer()
    mixer.fit_transform({})


def test_PipelineStepMixin_incorrect_dependencies() -> None:
    """Test fit-transform with incorrect dependencies."""

    class IncorrectMixer(PipelineStepMixin):
        """Test class for validation."""

        _DEPENDENCIES: ClassVar[Set[str]] = {"foobar"}

        def validate_input(self, input: List[str]) -> List[str]:
            return input

        def get_output_type(self, input_type: str) -> str:
            return input_type

        def _fit_transform(self, input: Dict[str, Dict]) -> Dict[str, Dict]:
            return {"input": input}

    mixer = IncorrectMixer()
    with pytest.raises(ImportError, match="not installed"):
        mixer.fit_transform({})


@pytest.mark.skipif(
    _check_afni() is False, reason="requires AFNI to be in PATH"
)
def test_PipelineStepMixin_correct_ext_dependencies() -> None:
    """Test fit-transform with correct external dependencies."""

    class CorrectMixer(PipelineStepMixin):
        """Test class for validation."""

        _EXT_DEPENDENCIES: ClassVar[List[Dict[str, str]]] = [{"name": "afni"}]

        def validate_input(self, input: List[str]) -> List[str]:
            return input

        def get_output_type(self, input_type: str) -> str:
            return input_type

        def _fit_transform(self, input: Dict[str, Dict]) -> Dict[str, Dict]:
            return {"input": input}

    mixer = CorrectMixer()
    mixer.fit_transform({})


@pytest.mark.skipif(
    _check_afni() is False, reason="requires AFNI to be in PATH"
)
def test_PipelineStepMixin_ext_deps_correct_commands() -> None:
    """Test fit-transform with correct external dependency commands."""

    class CorrectMixer(PipelineStepMixin):
        """Test class for validation."""

        _EXT_DEPENDENCIES: ClassVar[List[Dict[str, Union[str, List[str]]]]] = [
            {"name": "afni", "commands": ["3dReHo"]}
        ]

        def validate_input(self, input: List[str]) -> List[str]:
            return input

        def get_output_type(self, input_type: str) -> str:
            return input_type

        def _fit_transform(self, input: Dict[str, Dict]) -> Dict[str, Dict]:
            return {"input": input}

    mixer = CorrectMixer()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        mixer.fit_transform({})


@pytest.mark.skipif(
    _check_afni() is False, reason="requires AFNI to be in PATH"
)
def test_PipelineStepMixin_ext_deps_incorrect_commands() -> None:
    """Test fit-transform with inccorrect external dependency commands."""

    class CorrectMixer(PipelineStepMixin):
        """Test class for validation."""

        _EXT_DEPENDENCIES: ClassVar[List[Dict[str, Union[str, List[str]]]]] = [
            {"name": "afni", "commands": ["3d"]}
        ]

        def validate_input(self, input: List[str]) -> List[str]:
            return input

        def get_output_type(self, input_type: str) -> str:
            return input_type

        def _fit_transform(self, input: Dict[str, Dict]) -> Dict[str, Dict]:
            return {"input": input}

    mixer = CorrectMixer()
    with pytest.warns(RuntimeWarning, match="AFNI is installed"):
        mixer.fit_transform({})


def test_PipelineStepMixin_incorrect_ext_dependencies() -> None:
    """Test fit-transform with incorrect external dependencies."""

    class IncorrectMixer(PipelineStepMixin):
        """Test class for validation."""

        _EXT_DEPENDENCIES: ClassVar[List[Dict[str, Union[str, bool]]]] = [
            {"name": "foobar", "optional": True}
        ]

        def validate_input(self, input: List[str]) -> List[str]:
            return input

        def get_output_type(self, input_type: str) -> str:
            return input_type

        def _fit_transform(self, input: Dict[str, Dict]) -> Dict[str, Dict]:
            return {"input": input}

    mixer = IncorrectMixer()
    with pytest.raises(ValueError, match="Invalid value"):
        mixer.fit_transform({})


def test_PipelineStepMixin_correct_conditional_dependencies() -> None:
    """Test fit-transform with correct conditional dependencies."""

    class Dependency:
        _DEPENDENCIES: ClassVar[Set[str]] = {"math"}

    class CorrectMixer(PipelineStepMixin):
        """Test class for validation."""

        _CONDITIONAL_DEPENDENCIES: ClassVar[
            List[Dict[str, Union[str, Type]]]
        ] = [
            {
                "using": "math",
                "depends_on": Dependency,
            },
        ]

        using = "math"

        def validate_input(self, input: List[str]) -> List[str]:
            return input

        def get_output_type(self, input_type: str) -> str:
            return input_type

        def _fit_transform(self, input: Dict[str, Dict]) -> Dict[str, Dict]:
            return {"input": input}

    mixer = CorrectMixer()
    mixer.fit_transform({})


def test_PipelineStepMixin_incorrect_conditional_dependencies() -> None:
    """Test fit-transform with incorrect conditional dependencies."""

    class Dependency:
        _DEPENDENCIES: ClassVar[Set[str]] = {"math"}

    class IncorrectMixer(PipelineStepMixin):
        """Test class for validation."""

        _CONDITIONAL_DEPENDENCIES: ClassVar[
            List[Dict[str, Union[str, Type]]]
        ] = [
            {
                "using": "math",
                "depends_on": Dependency,
            },
        ]

        def validate_input(self, input: List[str]) -> List[str]:
            return input

        def get_output_type(self, input_type: str) -> str:
            return input_type

        def _fit_transform(self, input: Dict[str, Dict]) -> Dict[str, Dict]:
            return {"input": input}

    mixer = IncorrectMixer()
    with pytest.raises(AttributeError, match="`using`"):
        mixer.fit_transform({})


@pytest.mark.skipif(
    _check_afni() is False, reason="requires AFNI to be in PATH"
)
def test_PipelineStepMixin_correct_conditional_ext_dependencies() -> None:
    """Test fit-transform with correct conditional external dependencies."""

    class ExternalDependency:
        _EXT_DEPENDENCIES: ClassVar[List[Dict[str, str]]] = [{"name": "afni"}]

    class CorrectMixer(PipelineStepMixin):
        """Test class for validation."""

        _CONDITIONAL_DEPENDENCIES: ClassVar[
            List[Dict[str, Union[str, Type]]]
        ] = [
            {
                "using": "afni",
                "depends_on": ExternalDependency,
            },
        ]

        using = "afni"

        def validate_input(self, input: List[str]) -> List[str]:
            return input

        def get_output_type(self, input_type: str) -> str:
            return input_type

        def _fit_transform(self, input: Dict[str, Dict]) -> Dict[str, Dict]:
            return {"input": input}

    mixer = CorrectMixer()
    mixer.fit_transform({})
