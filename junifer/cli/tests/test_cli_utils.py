"""Provide tests for CLI utils."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import platform as pl
import sys

import pytest

from junifer._version import __version__
from junifer.cli.utils import (
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
    dependency_list = [
        "click",
        "numpy",
        "scipy",
        "datalad",
        "pandas",
        "nibabel",
        "nilearn",
        "sqlalchemy",
        "ruamel.yaml",
        "tqdm",
        "templateflow",
        "lapy",
        "lazy_loader",
        "looseversion",
        "junifer_data",
    ]

    if sys.version_info < (3, 11):
        dependency_list.append("importlib_metadata")

    assert frozenset(dependency_information.keys()) == frozenset(
        dependency_list
    )


def test_get_dependency_information_long() -> None:
    """Test long version of _get_dependency_information()."""
    dependency_information = _get_dependency_information(long_=True)
    dependency_information_keys = list(dependency_information.keys())
    dependency_list = [
        "click",
        "numpy",
        "scipy",
        "datalad",
        "pandas",
        "nibabel",
        "nilearn",
        "sqlalchemy",
        "ruamel.yaml",
        "tqdm",
        "templateflow",
        "lapy",
        "lazy_loader",
    ]
    for key in dependency_list:
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
