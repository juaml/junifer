"""Provide utility functions for the datagrabber sub-package."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Dict, List

from ..utils import logger, raise_error


# Define schema for pattern-based datagrabber's patterns
PATTERNS_SCHEMA = {
    "T1w": {
        "mandatory": ["pattern", "space"],
        "optional": ["mask_item"],
    },
    "T1w_mask": {
        "mandatory": ["pattern", "space"],
        "optional": [],
    },
    "T2w": {
        "mandatory": ["pattern", "space"],
        "optional": ["mask_item"],
    },
    "T2w_mask": {
        "mandatory": ["pattern", "space"],
        "optional": [],
    },
    "BOLD": {
        "mandatory": ["pattern", "space"],
        "optional": ["mask_item"],
    },
    "BOLD_confounds": {
        "mandatory": ["pattern", "format"],
        "optional": [],
    },
    "BOLD_mask": {
        "mandatory": ["pattern", "space"],
        "optional": [],
    },
    "Warp": {
        "mandatory": ["pattern", "src", "dst"],
        "optional": [],
    },
    "VBM_GM": {
        "mandatory": ["pattern", "space"],
        "optional": [],
    },
    "VBM_WM": {
        "mandatory": ["pattern", "space"],
        "optional": [],
    },
    "VBM_CSF": {
        "mandatory": ["pattern", "space"],
        "optional": [],
    },
    "DWI": {
        "mandatory": ["pattern"],
        "optional": [],
    },
}


def validate_types(types: List[str]) -> None:
    """Validate the types.

    Parameters
    ----------
    types : list of str
        The object to validate.

    Raises
    ------
    TypeError
        If ``types`` is not a list or if the values are not string.

    """
    if not isinstance(types, list):
        raise_error(msg="`types` must be a list", klass=TypeError)
    if any(not isinstance(x, str) for x in types):
        raise_error(msg="`types` must be a list of strings", klass=TypeError)


def validate_replacements(
    replacements: List[str], patterns: Dict[str, Dict[str, str]]
) -> None:
    """Validate the replacements.

    Parameters
    ----------
    replacements : list of str
        The object to validate.
    patterns : dict
        The patterns to validate against.

    Raises
    ------
    TypeError
        If ``replacements`` is not a list or if the values are not string.
    ValueError
        If a value in ``replacements`` is not part of a data type pattern or
        if no data type patterns contain all values in ``replacements``.

    """
    if not isinstance(replacements, list):
        raise_error(msg="`replacements` must be a list.", klass=TypeError)

    if any(not isinstance(x, str) for x in replacements):
        raise_error(
            msg="`replacements` must be a list of strings.", klass=TypeError
        )

    for x in replacements:
        if all(
            x not in y
            for y in [
                data_type_val["pattern"] for data_type_val in patterns.values()
            ]
        ):
            raise_error(msg=f"Replacement: {x} is not part of any pattern.")

    # Check that at least one pattern has all the replacements
    at_least_one = False
    for data_type_val in patterns.values():
        if all(x in data_type_val["pattern"] for x in replacements):
            at_least_one = True
    if at_least_one is False:
        raise_error(msg="At least one pattern must contain all replacements.")


def validate_patterns(
    types: List[str], patterns: Dict[str, Dict[str, str]]
) -> None:
    """Validate the patterns.

    Parameters
    ----------
    types : list of str
        The types list.
    patterns : dict
        The object to validate.

    Raises
    ------
    KeyError
        If any mandatory key is missing for a data type.
    RuntimeError
        If an unknown key is found for a data type.
    TypeError
        If ``patterns`` is not a dictionary.
    ValueError
        If length of ``types`` and ``patterns`` are different or
        if ``patterns`` is missing entries from ``types`` or
        if unknown data type is found in ``patterns`` or
        if data type pattern key contains '*' as value.

    """
    # Validate the types
    validate_types(types)
    if not isinstance(patterns, dict):
        raise_error(msg="`patterns` must be a dict.", klass=TypeError)
    # Unequal length of objects
    if len(types) > len(patterns):
        raise_error(
            msg="Length of `types` more than that of `patterns`.",
            klass=ValueError,
        )
    # Missing type in patterns
    if any(x not in patterns for x in types):
        raise_error(
            msg="`patterns` must contain all `types`", klass=ValueError
        )
    # Check against schema
    for data_type_key, data_type_val in patterns.items():
        # Check if valid data type is provided
        if data_type_key not in PATTERNS_SCHEMA:
            raise_error(
                f"Unknown data type: {data_type_key}, "
                f"should be one of: {list(PATTERNS_SCHEMA.keys())}"
            )
        # Check mandatory keys for data type
        for mandatory_key in PATTERNS_SCHEMA[data_type_key]["mandatory"]:
            if mandatory_key not in data_type_val:
                raise_error(
                    msg=(
                        f"Mandatory key: `{mandatory_key}` missing for "
                        f"{data_type_key}"
                    ),
                    klass=KeyError,
                )
            else:
                logger.debug(
                    f"Mandatory key: `{mandatory_key}` found for "
                    f"{data_type_key}"
                )
        # Check optional keys for data type
        for optional_key in PATTERNS_SCHEMA[data_type_key]["optional"]:
            if optional_key not in data_type_val:
                logger.debug(
                    f"Optional key: `{optional_key}` missing for "
                    f"{data_type_key}"
                )
            else:
                logger.debug(
                    f"Optional key: `{optional_key}` found for "
                    f"{data_type_key}"
                )
        # Check stray key for data type
        for key in data_type_val.keys():
            if key not in (
                PATTERNS_SCHEMA[data_type_key]["mandatory"]
                + PATTERNS_SCHEMA[data_type_key]["optional"]
            ):
                raise_error(
                    msg=(
                        f"Key: {key} not accepted for {data_type_key} "
                        "pattern, remove it to proceed"
                    ),
                    klass=RuntimeError,
                )
        # Wildcard check in patterns
        if "}*" in data_type_val["pattern"]:
            raise_error(
                msg=(
                    f"`{data_type_key}.pattern` must not contain `*` "
                    "following a replacement"
                ),
                klass=ValueError,
            )
