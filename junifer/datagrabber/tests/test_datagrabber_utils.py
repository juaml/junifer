"""Provide tests for utils."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from contextlib import nullcontext
from typing import ContextManager, Dict, List, Union

import pytest

from junifer.datagrabber.utils import (
    validate_patterns,
    validate_replacements,
    validate_types,
)


@pytest.mark.parametrize(
    "types, expect",
    [
        ("wrong", pytest.raises(TypeError, match="must be a list")),
        ([1], pytest.raises(TypeError, match="must be a list of strings")),
        (["T1w", "BOLD"], nullcontext()),
    ],
)
def test_validate_types(
    types: Union[str, List[str], List[int]],
    expect: ContextManager,
) -> None:
    """Test validation of types.

    Parameters
    ----------
    types : str, list of int or str
        The parametrized data types to validate.
    expect : typing.ContextManager
        The parametrized ContextManager object.

    """
    with expect:
        validate_types(types)  # type: ignore


@pytest.mark.parametrize(
    "replacements, patterns, expect",
    [
        (
            "wrong",
            "also wrong",
            pytest.raises(TypeError, match="must be a list"),
        ),
        (
            [1],
            {
                "T1w": {"pattern": "{subject}/anat/{subject}_T1w.nii.gz"},
                "BOLD": {
                    "pattern": "{subject}/func/{subject}_task-rest_bold.nii.gz"
                },
            },
            pytest.raises(TypeError, match="must be a list of strings"),
        ),
        (
            ["session"],
            {
                "T1w": {"pattern": "{subject}/anat/{subject}_T1w.nii.gz"},
                "BOLD": {
                    "pattern": "{subject}/func/{subject}_task-rest_bold.nii.gz"
                },
            },
            pytest.raises(ValueError, match="is not part of"),
        ),
        (
            ["subject", "session"],
            {
                "T1w": {"pattern": "{subject}/anat/_T1w.nii.gz"},
                "BOLD": {"pattern": "{session}/func/_task-rest_bold.nii.gz"},
            },
            pytest.raises(ValueError, match="At least one pattern"),
        ),
        (
            ["subject"],
            {
                "T1w": {"pattern": "{subject}/anat/{subject}_T1w.nii.gz"},
                "BOLD": {
                    "pattern": "{subject}/func/{subject}_task-rest_bold.nii.gz"
                },
            },
            nullcontext(),
        ),
    ],
)
def test_validate_replacements(
    replacements: Union[str, List[str], List[int]],
    patterns: Union[str, Dict[str, Dict[str, str]]],
    expect: ContextManager,
) -> None:
    """Test validation of replacements.

    Parameters
    ----------
    replacements : str, list of str or int
        The parametrized pattern replacements to validate.
    patterns : str, dict
        The parametrized patterns to validate against.
    expect : typing.ContextManager
        The parametrized ContextManager object.

    """
    with expect:
        validate_replacements(replacements=replacements, patterns=patterns)  # type: ignore


@pytest.mark.parametrize(
    "types, patterns, expect",
    [
        (
            ["T1w", "BOLD"],
            "wrong",
            pytest.raises(TypeError, match="must be a dict"),
        ),
        (
            ["T1w", "BOLD"],
            {
                "T1w": {"pattern": "{subject}/anat/{subject}_T1w.nii.gz"},
            },
            pytest.raises(
                ValueError,
                match="Length of `types` more than that of `patterns`.",
            ),
        ),
        (
            ["T1w", "BOLD"],
            {
                "T1w": {"pattern": "{subject}/anat/{subject}_T1w.nii.gz"},
                "T2w": {"pattern": "{subject}/anat/{subject}_T2w.nii.gz"},
            },
            pytest.raises(ValueError, match="contain all"),
        ),
        (
            ["T3w"],
            {
                "T3w": {"pattern": "{subject}/anat/{subject}_T3w.nii.gz"},
            },
            pytest.raises(ValueError, match="Unknown data type"),
        ),
        (
            ["BOLD"],
            {
                "BOLD": {"patterns": "{subject}/func/{subject}_BOLD.nii.gz"},
            },
            pytest.raises(KeyError, match="Mandatory key"),
        ),
        (
            ["BOLD_confounds"],
            {
                "BOLD_confounds": {
                    "pattern": "{subject}/func/{subject}_confounds.tsv",
                    "format": "fmriprep",
                    "space": "MNINLin6Asym",
                },
            },
            pytest.raises(RuntimeError, match="not accepted"),
        ),
        (
            ["T1w"],
            {
                "T1w": {
                    "pattern": "{subject}/anat/{subject}*.nii",
                    "space": "native",
                },
            },
            pytest.raises(ValueError, match="following a replacement"),
        ),
        (
            ["T1w", "T2w", "BOLD", "BOLD_confounds"],
            {
                "T1w": {
                    "pattern": "{subject}/anat/{subject}_T1w.nii.gz",
                    "space": "native",
                },
                "T2w": {
                    "pattern": "{subject}/anat/{subject}_T2w.nii.gz",
                    "space": "native",
                },
                "BOLD": {
                    "pattern": (
                        "{subject}/func/{subject}_task-rest_bold.nii.gz"
                    ),
                    "space": "MNI152NLin6Asym",
                },
                "BOLD_confounds": {
                    "pattern": "{subject}/func/{subject}_confounds.tsv",
                    "format": "fmriprep",
                },
            },
            nullcontext(),
        ),
    ],
)
def test_validate_patterns(
    types: List[str],
    patterns: Union[str, Dict[str, Dict[str, str]]],
    expect: ContextManager,
) -> None:
    """Test validation of patterns.

    Parameters
    ----------
    types : list of str
        The parametrized data types.
    patterns : str, dict
        The patterns to validate.
    expect : typing.ContextManager
        The parametrized ContextManager object.

    """
    with expect:
        validate_patterns(types=types, patterns=patterns)  # type: ignore
