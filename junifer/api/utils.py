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


def _get_dependency_information(long_: bool) -> Dict[str, str]:
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
        for key in [
            "click",
            "numpy",
            "datalad",
            "pandas",
            "nibabel",
            "nilearn",
            "sqlalchemy",
            "pyyaml",
        ]:
            if key in dependency_versions.keys():
                pruned_dependency_versions[key] = dependency_versions[key]

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
    for key, value in os.environ.items():
        environment_values[key] = value

    return environment_values
