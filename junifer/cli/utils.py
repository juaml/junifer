"""Provide utility functions for the cli sub-package."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import os
import platform as pl
import re
from importlib.metadata import distribution
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


def _get_environment_information(long_: bool) -> Dict[str, str]:
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


def _setup_component_registry() -> None:
    """Set up the pipeline component registry."""

    from junifer.datagrabber import (
        HCP1200,  # noqa: F401
        BaseDataGrabber,  # noqa: F401
        DataladAOMICID1000,  # noqa: F401
        DataladAOMICPIOP1,  # noqa: F401
        DataladAOMICPIOP2,  # noqa: F401
        DataladDataGrabber,  # noqa: F401
        DataladHCP1200,  # noqa: F401
        DMCC13Benchmark,  # noqa: F401
        MultipleDataGrabber,  # noqa: F401
        PatternDataGrabber,  # noqa: F401
        PatternDataladDataGrabber,  # noqa: F401
    )
    from junifer.datareader import DefaultDataReader  # noqa: F401
    from junifer.markers import (
        ALFFParcels,  # noqa: F401
        ALFFSpheres,  # noqa: F401
        BaseMarker,  # noqa: F401
        BrainPrint,  # noqa: F401
        CrossParcellationFC,  # noqa: F401
        EdgeCentricFCParcels,  # noqa: F401
        EdgeCentricFCSpheres,  # noqa: F401
        FunctionalConnectivityParcels,  # noqa: F401
        FunctionalConnectivitySpheres,  # noqa: F401
        ParcelAggregation,  # noqa: F401
        ReHoParcels,  # noqa: F401
        ReHoSpheres,  # noqa: F401
        RSSETSMarker,  # noqa: F401
        SphereAggregation,  # noqa: F401
        TemporalSNRParcels,  # noqa: F401
        TemporalSNRSpheres,  # noqa: F401
    )
    from junifer.preprocess import (
        BasePreprocessor,  # noqa: F401
        Smoothing,  # noqa: F401
        SpaceWarper,  # noqa: F401
        fMRIPrepConfoundRemover,  # noqa: F401
    )
    from junifer.storage import (
        BaseFeatureStorage,  # noqa: F401
        HDF5FeatureStorage,  # noqa: F401
        PandasBaseFeatureStorage,  # noqa: F401
        SQLiteFeatureStorage,  # noqa: F401
    )
