"""Provide utility functions for pipeline sub-package."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
#          Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

import subprocess
from typing import Any, Optional

from junifer.utils.logging import raise_error, warn_with_log


__all__ = ["check_ext_dependencies"]


def check_ext_dependencies(
    name: str, optional: bool = False, **kwargs: Any
) -> bool:
    """Check if external dependency `name` is found if mandatory.

    Parameters
    ----------
    name : str
        The name of the dependency.
    optional : bool, optional
        Whether the dependency is optional (default False).
    **kwargs : dict
        Extra keyword arguments.

    Returns
    -------
    bool
        Whether the external dependency was found.

    Raises
    ------
    ValueError
        If ``name`` is invalid.
    RuntimeError
        If ``name`` is mandatory and is not found.

    """
    valid_ext_dependencies = ("afni", "fsl", "ants", "freesurfer")
    if name not in valid_ext_dependencies:
        raise_error(
            "Invalid value for `name`, should be one of: "
            f"{valid_ext_dependencies}"
        )
    # Check for afni
    if name == "afni":
        found = _check_afni(**kwargs)
    # Check for fsl
    elif name == "fsl":
        found = _check_fsl(**kwargs)
    # Check for ants
    elif name == "ants":
        found = _check_ants(**kwargs)
    # Check for freesurfer
    elif name == "freesurfer":
        found = _check_freesurfer(**kwargs)

    # Check if the dependency is mandatory in case it's not found
    if not found and not optional:
        raise_error(
            msg=(
                f"{name} is not installed but is "
                "required by one of the pipeline steps"
            ),
            klass=RuntimeError,
        )
    return found


def _check_afni(commands: Optional[list[str]] = None) -> bool:
    """Check if AFNI is present in the system.

    Parameters
    ----------
    commands : list of str, optional
        The commands to specifically check for from AFNI. If None, only
        the basic afni version would be looked up, else, would also
        check for specific commands (default None).

    Returns
    -------
    bool
        Whether afni is found or not.

    """
    completed_process = subprocess.run(
        "afni --version",
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        shell=True,  # is unsafe but kept for resolution via PATH
        check=False,
    )
    afni_found = completed_process.returncode == 0

    # Check for specific commands
    if afni_found and commands is not None:
        if not isinstance(commands, list):
            commands = [commands]
        # Store command found results
        commands_found_results = {}
        # Set all commands found flag to True
        all_commands_found = True
        # Check commands' existence
        for command in commands:
            command_process = subprocess.run(
                [command],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
                shell=True,  # is unsafe but kept for resolution via PATH
                check=False,
            )
            command_found = command_process.returncode == 0
            commands_found_results[command] = (
                "found" if command_found else "not found"
            )
            # Set flag to trigger warning
            all_commands_found = all_commands_found and command_found
        # One or more commands were missing
        if not all_commands_found:
            warn_with_log(
                "AFNI is installed but some of the required commands "
                "were not found. These are the results: "
                f"{commands_found_results}"
            )
    return afni_found


def _check_fsl(commands: Optional[list[str]] = None) -> bool:
    """Check if FSL is present in the system.

    Parameters
    ----------
    commands : list of str, optional
        The commands to specifically check for from FSL. If None, only
        the basic FSL flirt version would be looked up, else, would also
        check for specific commands (default None).

    Returns
    -------
    bool
        Whether FSL is found or not.

    """
    completed_process = subprocess.run(
        "flirt",
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        shell=True,  # is unsafe but kept for resolution via PATH
        check=False,
    )
    fsl_found = completed_process.returncode == 1

    # Check for specific commands
    if fsl_found and commands is not None:
        if not isinstance(commands, list):
            commands = [commands]
        # Store command found results
        commands_found_results = {}
        # Set all commands found flag to True
        all_commands_found = True
        # Check commands' existence
        for command in commands:
            command_process = subprocess.run(
                [command],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
                shell=True,  # is unsafe but kept for resolution via PATH
                check=False,
            )
            # FSL commands are incoherent with respect to status code hence a
            # blanket to only look for no command found
            command_found = command_process.returncode != 127
            commands_found_results[command] = (
                "found" if command_found else "not found"
            )
            # Set flag to trigger warning
            all_commands_found = all_commands_found and command_found
        # One or more commands were missing
        if not all_commands_found:
            warn_with_log(
                "FSL is installed but some of the required commands "
                "were not found. These are the results: "
                f"{commands_found_results}"
            )
    return fsl_found


def _check_ants(commands: Optional[list[str]] = None) -> bool:
    """Check if ANTs is present in the system.

    Parameters
    ----------
    commands : list of str, optional
        The commands to specifically check for from ANTs. If None, only
        the basic ANTS help would be looked up, else, would also
        check for specific commands (default None).

    Returns
    -------
    bool
        Whether ANTs is found or not.

    """
    completed_process = subprocess.run(
        "ANTS --help",
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        shell=True,  # is unsafe but kept for resolution via PATH
        check=False,
    )
    ants_found = completed_process.returncode == 0

    # Check for specific commands
    if ants_found and commands is not None:
        if not isinstance(commands, list):
            commands = [commands]
        # Store command found results
        commands_found_results = {}
        # Set all commands found flag to True
        all_commands_found = True
        # Check commands' existence
        for command in commands:
            command_process = subprocess.run(
                [command],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
                shell=True,  # is unsafe but kept for resolution via PATH
                check=False,
            )
            command_found = command_process.returncode == 1
            commands_found_results[command] = (
                "found" if command_found else "not found"
            )
            # Set flag to trigger warning
            all_commands_found = all_commands_found and command_found
        # One or more commands were missing
        if not all_commands_found:
            warn_with_log(
                "ANTs is installed but some of the required commands "
                "were not found. These are the results: "
                f"{commands_found_results}"
            )
    return ants_found


def _check_freesurfer(commands: Optional[list[str]] = None) -> bool:
    """Check if FreeSurfer is present in the system.

    Parameters
    ----------
    commands : list of str, optional
        The commands to specifically check for from FreeSurfer. If None, only
        the basic FreeSurfer help would be looked up, else, would also
        check for specific commands (default None).

    Returns
    -------
    bool
        Whether FreeSurfer is found or not.

    """
    completed_process = subprocess.run(
        "recon-all -help",
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        shell=True,  # is unsafe but kept for resolution via PATH
        check=False,
    )
    fs_found = completed_process.returncode == 0

    # Check for specific commands
    if fs_found and commands is not None:
        if not isinstance(commands, list):
            commands = [commands]
        # Store command found results
        commands_found_results = {}
        # Set all commands found flag to True
        all_commands_found = True
        # Check commands' existence
        for command in commands:
            command_process = subprocess.run(
                [command],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
                shell=True,  # is unsafe but kept for resolution via PATH
                check=False,
            )
            command_found = command_process.returncode == 0
            commands_found_results[command] = (
                "found" if command_found else "not found"
            )
            # Set flag to trigger warning
            all_commands_found = all_commands_found and command_found
        # One or more commands were missing
        if not all_commands_found:
            warn_with_log(
                "FreeSurfer is installed but some of the required commands "
                "were not found. These are the results: "
                f"{commands_found_results}"
            )
    return fs_found
