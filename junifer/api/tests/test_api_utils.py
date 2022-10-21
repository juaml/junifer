"""Provide tests for utils."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import platform as pl

import pytest

from junifer._version import __version__
from junifer.api.utils import (
    _get_dependency_information,
    _get_environment_information,
    _get_junifer_version,
    _get_python_information,
    _get_system_information,
)


def test_get_junifer_version() -> None:
    """Test _get_junifer_version()."""
    assert _get_junifer_version()["version"] == __version__


def test_get_python_information() -> None:
    """Test _get_python_information()."""
    python_information = _get_python_information()
    assert python_information["version"] == pl.python_version()
    assert python_information["implementation"] == pl.python_implementation()


def test_get_dependency_information_short() -> None:
    """Test short version of _get_dependency_information()."""
    dependency_information = _get_dependency_information(long_=False)
    assert [key for key in dependency_information.keys()] == [
        "click",
        "numpy",
        "datalad",
        "pandas",
        "nibabel",
        "nilearn",
        "sqlalchemy",
        "yaml",
    ]


def test_get_dependency_information_long() -> None:
    """Test long version of _get_dependency_information()."""
    dependency_information = _get_dependency_information(long_=True)
    dependency_information_keys = [
        key for key in dependency_information.keys()
    ]
    for key in [
        "click",
        "numpy",
        "datalad",
        "pandas",
        "nibabel",
        "nilearn",
        "sqlalchemy",
        "yaml",
    ]:
        assert key in dependency_information_keys


def test_get_system_information() -> None:
    """Test _get_system_information()."""
    system_information = _get_system_information()
    assert system_information["platform"] == pl.platform()


@pytest.mark.parametrize(
    "format_",
    [
        "short",
        "long",
    ],
)
def test_get_environment_information(format_: str) -> None:
    """Test _get_environment_information().

    Parameters
    ----------
    format_ : str
        The parametrized report version.

    """
    environment_information = _get_environment_information(long_=format_)
    assert "PATH" in environment_information.keys()
