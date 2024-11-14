"""Provide tests for PatternValidationMixin."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from contextlib import AbstractContextManager, nullcontext
from typing import Union

import pytest

from junifer.datagrabber.pattern_validation_mixin import PatternValidationMixin


@pytest.mark.parametrize(
    "types, replacements, patterns, expect",
    [
        (
            "wrong",
            [],
            {},
            pytest.raises(TypeError, match="`types` must be a list"),
        ),
        (
            [1],
            [],
            {},
            pytest.raises(
                TypeError, match="`types` must be a list of strings"
            ),
        ),
        (
            ["BOLD"],
            [],
            "wrong",
            pytest.raises(TypeError, match="`patterns` must be a dict"),
        ),
        (
            ["T1w", "BOLD"],
            "",
            {
                "T1w": {"pattern": "{subject}/anat/{subject}_T1w.nii.gz"},
            },
            pytest.raises(
                ValueError,
                match="Length of `types` more than that of `patterns`",
            ),
        ),
        (
            ["T1w", "BOLD"],
            "",
            {
                "T1w": {"pattern": "{subject}/anat/{subject}_T1w.nii.gz"},
                "T2w": {"pattern": "{subject}/anat/{subject}_T2w.nii.gz"},
            },
            pytest.raises(
                ValueError, match="`patterns` must contain all `types`"
            ),
        ),
        (
            ["T3w"],
            "",
            {
                "T3w": {"pattern": "{subject}/anat/{subject}_T3w.nii.gz"},
            },
            pytest.raises(ValueError, match="Unknown data type"),
        ),
        (
            ["BOLD"],
            "",
            {
                "BOLD": {"patterns": "{subject}/func/{subject}_BOLD.nii.gz"},
            },
            pytest.raises(KeyError, match="Mandatory key"),
        ),
        (
            ["BOLD"],
            "",
            {
                "BOLD": {
                    "pattern": (
                        "{subject}/func/{subject}_task-rest_bold.nii.gz"
                    ),
                    "space": "MNINLin6Asym",
                    "confounds": {
                        "pattern": "{subject}/func/{subject}_confounds.tsv",
                        "format": "fmriprep",
                    },
                    "zip": "zap",
                },
            },
            pytest.raises(RuntimeError, match="not accepted"),
        ),
        (
            ["T1w"],
            "",
            {
                "T1w": {
                    "pattern": "{subject}/anat/{subject}*.nii",
                    "space": "native",
                },
            },
            pytest.raises(ValueError, match="following a replacement"),
        ),
        (
            ["T1w"],
            "wrong",
            {
                "T1w": {
                    "pattern": "{subject}/anat/{subject}_T1w.nii",
                    "space": "native",
                },
            },
            pytest.raises(TypeError, match="`replacements` must be a list"),
        ),
        (
            ["T1w"],
            [1],
            {
                "T1w": {
                    "pattern": "{subject}/anat/{subject}_T1w.nii",
                    "space": "native",
                },
            },
            pytest.raises(
                TypeError, match="`replacements` must be a list of strings"
            ),
        ),
        (
            ["T1w", "BOLD"],
            ["subject", "session"],
            {
                "T1w": {
                    "pattern": "{subject}/anat/{subject}_T1w.nii.gz",
                    "space": "native",
                },
                "BOLD": {
                    "pattern": (
                        "{subject}/func/{subject}_task-rest_bold.nii.gz"
                    ),
                    "space": "MNI152NLin6Asym",
                },
            },
            pytest.raises(ValueError, match="is not part of any pattern"),
        ),
        (
            ["BOLD"],
            ["subject", "session"],
            {
                "T1w": {
                    "pattern": "{subject}/anat/_T1w.nii.gz",
                    "space": "native",
                },
                "BOLD": {
                    "pattern": "{session}/func/_task-rest_bold.nii.gz",
                    "space": "MNI152NLin6Asym",
                },
            },
            pytest.raises(ValueError, match="At least one pattern"),
        ),
        (
            ["T1w", "T2w", "BOLD"],
            ["subject"],
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
                        "{subject}/func/{session}/{subject}_task-rest_bold.nii.gz"
                    ),
                    "space": "MNI152NLin6Asym",
                    "confounds": {
                        "pattern": "{subject}/func/{subject}_confounds.tsv",
                        "format": "fmriprep",
                    },
                },
            },
            nullcontext(),
        ),
    ],
)
def test_PatternValidationMixin(
    types: Union[str, list[str], list[int]],
    replacements: Union[str, list[str], list[int]],
    patterns: Union[str, dict[str, dict[str, str]]],
    expect: AbstractContextManager,
) -> None:
    """Test validation.

    Parameters
    ----------
    types : str, list of int or str
        The parametrized data types to validate.
    replacements : str, list of str or int
        The parametrized pattern replacements to validate.
    patterns : str, dict
        The parametrized patterns to validate against.
    expect : typing.ContextManager
        The parametrized ContextManager object.

    """

    class MockDataGrabber(PatternValidationMixin):
        def __init__(
            self,
            types,
            replacements,
            patterns,
        ) -> None:
            self.types = types
            self.replacements = replacements
            self.patterns = patterns

        def validate(self) -> None:
            self.validate_patterns(
                types=self.types,
                replacements=self.replacements,
                patterns=self.patterns,
            )

    dg = MockDataGrabber(types, replacements, patterns)
    with expect:
        dg.validate()


# This test is kept separate as bool doesn't support context manager protocol,
# used in the earlier test
def test_PatternValidationMixin_partial_pattern_check() -> None:
    """Test validation for partial patterns."""
    with pytest.warns(RuntimeWarning, match="might not work as expected"):
        PatternValidationMixin().validate_patterns(
            types=["BOLD"],
            replacements=["subject"],
            patterns={
                "BOLD": {
                    "mask": {
                        "pattern": "{subject}/func/{subject}_BOLD.nii.gz",
                        "space": "MNI152NLin6Asym",
                    },
                },
            },  # type: ignore
            partial_pattern_ok=True,
        )
