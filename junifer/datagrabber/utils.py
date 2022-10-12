"""Provide utility functions for the datagrabber sub-package."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Dict, List, Union

from ..utils import raise_error


def validate_types(types: List[str]) -> None:
    """Validate the types.

    Parameters
    ----------
    types : list of str
        The object to validate.

    """
    if not isinstance(types, list):
        raise_error(msg="`types` must be a list", klass=TypeError)
    if any(not isinstance(x, str) for x in types):
        raise_error(msg="`types` must be a list of strings", klass=TypeError)


def validate_replacements(
    replacements: List[str], patterns: Dict[str, str]
) -> None:
    """Validate the replacements.

    Parameters
    ----------
    replacements : list of str
        The object to validate.
    patterns : dict
        The patterns to validate against.

    """
    if not isinstance(replacements, list):
        raise_error(msg="`replacements` must be a list.", klass=TypeError)

    if not isinstance(patterns, dict):
        raise_error(msg="`patterns` must be a dict.", klass=TypeError)

    if any(not isinstance(x, str) for x in replacements):
        raise_error(
            msg="`replacements` must be a list of strings.", klass=TypeError
        )

    for x in replacements:
        if all(x not in y for y in patterns.values()):
            raise_error(msg=f"Replacement {x} is not part of any pattern.")

    # Check that at least one pattern has all the replacements
    at_least_one = False
    for _, v in patterns.items():
        if all(x in v for x in replacements):
            at_least_one = True
    if at_least_one is False:
        raise_error(msg="At least one pattern must contain all replacements.")


def validate_patterns(types: List[str], patterns: Dict[str, str]) -> None:
    """Validate the patterns.

    Parameters
    ----------
    types : list of str
        The types list.
    patterns : dict
        The object to validate.

    """
    # Validate the types
    validate_types(types)
    if not isinstance(patterns, dict):
        raise_error(msg="`patterns` must be a dict.", klass=TypeError)
    # Unequal length of objects
    if len(types) != len(patterns):
        raise_error(
            msg="`types` and `patterns` must have the same length.",
            klass=ValueError,
        )

    if any(x not in patterns for x in types):
        raise_error(
            msg="`patterns` must contain all `types`", klass=ValueError
        )

    if any("}*" in pattern for pattern in patterns.values()):
        raise_error(
            msg="`patterns` must not contain `*` following a replacement",
            klass=ValueError,
        )


def validate_and_format_parameters(
    params: Union[List[str], None, str],
    valid_params: List[str],
    error_msg: str,
) -> List[str]:
    """Validate and format datagrabber parameters.

    Parameters
    ----------
    params : str, list of str, None
        The parameters handed to the datagrabber.
    valid_params : list of str
        The list of accepted parameter values
    error_msg : str
        error message if a parameter is not accepted.

    """

    if params is None:
        params = valid_params
    else:
        if isinstance(params, str):
            params = [params]
        for p in params:
            if p not in valid_params:
                raise_error(error_msg)

    return params
