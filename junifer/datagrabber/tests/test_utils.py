"""Provide tests for datagrabber/utils."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import pytest

from junifer.datagrabber.utils import validate_and_format_parameters


def test_validate_and_format_none():
    """Test validate_and_format_parameters if None."""

    valid_params = ["p1", "p2", "p3"]
    validated = validate_and_format_parameters(
        None,
        valid_params,
        "Invalid parameter, valid_parameters are {valid_params}",
    )
    assert valid_params == validated


def test_validate_and_format_str():
    """Test validate_and_format_parameters if str."""
    valid_params = ["p1", "p2", "p3"]
    validated = validate_and_format_parameters(
        "p1",
        valid_params,
        "Invalid parameter, valid_parameters are {valid_params}",
    )
    assert ["p1"] == validated


def test_validate_and_format_list():
    """Test validate_and_format_parameters if list."""
    valid_params = ["p1", "p2", "p3"]
    validated = validate_and_format_parameters(
        ["p1", "p2"],
        valid_params,
        "Invalid parameter, valid_parameters are {valid_params}",
    )
    assert ["p1", "p2"] == validated


def test_validate_and_format_invalid():
    """Test validate_and_format_parameters if invalid."""
    with pytest.raises(ValueError, match="Invalid parameter, "):
        valid_params = ["p1", "p2", "p3"]
        validate_and_format_parameters(
            "invalid",
            valid_params,
            "Invalid parameter, valid_parameters are {valid_params}",
        )
