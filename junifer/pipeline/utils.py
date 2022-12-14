"""Provide utility functions for pipeline sub-package."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
#          Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

import subprocess
from typing import Any, List, Optional

from junifer.utils.logging import raise_error, warn_with_log


def check_ext_dependencies(name: str, optional: bool, **kwargs: Any) -> bool:
    """Check if external dependency `name` is found if mandatory.

    Parameters
    ----------
    name : str
        The name of the dependency.
    optional : bool
        Whether the dependency is optional. For external dependencies marked
        as optional, there should be an implementation provided with junfier.
    **kwargs : dict
        Extra keyword arguments.

    Returns
    -------
    bool
        Whether the external dependency was found.

    """
    # Check for afni
    if name == "afni":
        found = _check_afni(**kwargs)
    # Went off the rails
    else:
        raise_error(
            f"The external dependency {name} has no check. "
            f"Either the name '{name}' is incorrect or you were too "
            "adventurous. Raise an issue if it's the latter ;-)."
        )
    # Check if the dependency is mandatory in case it's not found
    if not found and not optional:
        raise_error(
            f"{name} is not installed but is "
            "required by one of the pipeline steps."
        )
    return found


def _check_afni(commands: Optional[List[str]] = None) -> bool:
    """Check if afni is present in the system.

    Parameters
    ----------
    commands : list of str, optional
        The commands to specifically check for from afni. If None, only
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
