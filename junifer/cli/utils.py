"""Provide utility functions for the cli sub-package."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import os
import platform as pl
import re
from importlib.metadata import distribution

from .._version import __version__
from ..utils.logging import get_versions


def _get_junifer_version() -> dict[str, str]:
    """Get junifer version information.

    Returns
    -------
    dict
        A dictionary containing junifer version.

    """
    return {
        "version": __version__,
    }


def _get_python_information() -> dict[str, str]:
    """Get installed Python information.

    Parameters
    ----------
    dict
        A dictionary containing Python information.

    """
    return {
        "version": pl.python_version(),
        "implementation": pl.python_implementation(),
    }


def _get_dependency_information(long_: bool) -> dict[str, str]:
    """Get Python environment dependency information.

    Parameters
    ----------
    long_ : bool
        Whether to report long version.

    Returns
    -------
    dict
        A dictionary containing Python dependency information.

    """
    dependency_versions = get_versions()

    pruned_dependency_versions = {}
    # Report long version
    if long_:
        for key, value in dependency_versions.items():
            # Ignore built-in modules and self
            if value != "None" and key != "junifer":
                pruned_dependency_versions[key] = value

    # Report short version
    else:
        # Get dependencies for junifer
        dist = distribution("junifer")
        # Compile regex pattern
        re_pattern = re.compile("[a-z-_.]+")

        for pkg_with_version in dist.requires:  # type: ignore
            # Perform regex search
            matches = re.findall(pattern=re_pattern, string=pkg_with_version)
            # Extract package name
            key = matches[0]

            if key in dependency_versions.keys():
                # Check if pkg part of optional dependencies
                if "extra" not in matches:
                    pruned_dependency_versions[key] = dependency_versions[key]

    return pruned_dependency_versions


def _get_system_information() -> dict[str, str]:
    """Get system information.

    Returns
    -------
    dict
        A dictionary containing system information.

    """
    return {
        "platform": pl.platform(),
    }


def _get_environment_information(long_: bool) -> dict[str, str]:
    """Get system environment information.

    Parameters
    ----------
    long_ : bool
        Whether to report long version.

    Returns
    -------
    dict
        A dictionary containing system environment information.

    """
    environment_values = {}
    # Report long version
    if long_:
        for key, value in os.environ.items():
            environment_values[key] = value
    # Report short version
    else:
        for key in ["LC_CTYPE", "LC_TERMINAL", "LC_TERMINAL_VERSION", "PATH"]:
            if key in os.environ.keys():
                environment_values[key] = os.environ[key]

    return environment_values
