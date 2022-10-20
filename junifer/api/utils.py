"""Provide utility functions for the api sub-package."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import os
import platform as pl
from typing import Dict

from .._version import __version__
from ..utils.logging import get_versions


def _get_junifer_version() -> Dict[str, str]:
    """Get junifer version information.

    Returns
    -------
    dict
        A dictionary containing junifer version.

    """
    return {
        "version": __version__,
    }


def _get_python_information() -> Dict[str, str]:
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


def _get_dependency_information() -> Dict[str, str]:
    """Get Python environment dependency information.

    Returns
    -------
    dict
        A dictionary containing Python dependency information.

    """
    dependency_versions = get_versions()

    pruned_dependency_versions = {}
    for key, value in dependency_versions.items():
        # Ignore built-in modules and self
        if value != "None" and key != "junifer":
            pruned_dependency_versions[key] = value

    return pruned_dependency_versions


def _get_system_information() -> Dict[str, str]:
    """Get system information.

    Returns
    -------
    dict
        A dictionary containing system information.

    """
    return {
        "platform": pl.platform(),
    }


def _get_environment_information() -> Dict[str, str]:
    """Get system environment information.

    Returns
    -------
    dict
        A dictionary containing system environment information.

    """
    environment_values = {}
    for key in ["LC_CTYPE", "LC_TERMINAL", "LC_TERMINAL_VERSION", "PATH"]:
        if key in os.environ.keys():
            environment_values[key] = os.environ[key]

    return environment_values
