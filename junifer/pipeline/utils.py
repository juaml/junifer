"""Provide utility functions for pipeline sub-package."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
#          Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

import subprocess
from typing import Any

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


def _check_afni(commands=None) -> bool:
    """Check if afni is present in the system.

    Returns
    -------
    bool
        Whether afni is found or not.

    """
    completed_process = subprocess.run(
        ["afni", "--version"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        shell=True,  # is unsafe but kept for resolution via PATH
        check=False,
    )
    afni_found = completed_process.returncode == 0

    if afni_found and commands is not None:
        if not isinstance(commands, list):
            commands = [commands]
        cmd_results = {}
        cmds_found = True
        for command in commands:
            completed_process = subprocess.run(
                [command],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
                shell=True,  # is unsafe but kept for resolution via PATH
                check=False,
            )
            t_cmd_found = completed_process.returncode == 0
            cmd_results[command] = "found" if t_cmd_found else "not found"
            cmds_found = cmds_found and t_cmd_found
        if not cmds_found:
            warn_with_log(
                f"AFNI is installed but some of the required commands "
                f"are not found. These are the results: {cmd_results}"
            )
    return afni_found
