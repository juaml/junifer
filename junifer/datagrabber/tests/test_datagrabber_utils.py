"""Provide tests for utils."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

import pytest

from junifer.datagrabber.utils import (
    validate_patterns,
    validate_replacements,
    validate_types,
)


def test_validate_types() -> None:
    """Test validation of types."""
    with pytest.raises(TypeError, match="must be a list"):
        validate_types("wrong")  # type: ignore
    with pytest.raises(TypeError, match="must be a list of strings"):
        validate_types([1])  # type: ignore

    validate_types(["T1w", "BOLD"])


def test_validate_replacements() -> None:
    """Test validation of replacements."""
    with pytest.raises(TypeError, match="must be a list"):
        validate_replacements("wrong", "also wrong")  # type: ignore
    with pytest.raises(TypeError, match="must be a dict"):
        validate_replacements(["correct"], "wrong")  # type: ignore

    patterns = {
        "T1w": "{subject}/anat/{subject}_T1w.nii.gz",
        "BOLD": "{subject}/func/{subject}_task-rest_bold.nii.gz",
    }

    with pytest.raises(TypeError, match="must be a list of strings"):
        validate_replacements([1], patterns)  # type: ignore

    with pytest.raises(ValueError, match="is not part of"):
        validate_replacements(["session"], patterns)

    wrong_patterns = {
        "T1w": "{subject}/anat/_T1w.nii.gz",
        "BOLD": "{session}/func/_task-rest_bold.nii.gz",
    }

    with pytest.raises(ValueError, match="At least one pattern"):
        validate_replacements(["subject", "session"], wrong_patterns)

    validate_replacements(["subject"], patterns)


def test_validate_patterns() -> None:
    """Test validation of patterns."""
    types = ["T1w", "BOLD"]
    with pytest.raises(TypeError, match="must be a dict"):
        validate_patterns(types, "wrong")  # type: ignore

    wrongpatterns = {
        "T1w": "{subject}/anat/{subject}_T1w.nii.gz",
    }

    with pytest.raises(ValueError, match="same length"):
        validate_patterns(types, wrongpatterns)  # type: ignore

    wrongpatterns = {
        "T1w": "{subject}/anat/{subject}_T1w.nii.gz",
        "T2": "{subject}/anat/{subject}_T2.nii.gz",
    }

    with pytest.raises(ValueError, match="contain all"):
        validate_patterns(types, wrongpatterns)  # type: ignore

    patterns = {
        "T1w": "{subject}/anat/{subject}_T1w.nii.gz",
        "BOLD": "{subject}/func/{subject}_task-rest_bold.nii.gz",
    }

    wrongpatterns = {
        "T1w": "{subject}/anat/{subject}*.nii",
        "BOLD": "{subject}/func/{subject}_task-rest_bold.nii.gz",
    }

    with pytest.raises(ValueError, match="following a replacement"):
        validate_patterns(types, wrongpatterns)

    validate_patterns(types, patterns)
