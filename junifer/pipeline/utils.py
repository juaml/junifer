"""Provide utility functions for pipeline sub-package."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
#          Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

import subprocess
from junifer.utils.logging import raise_error


def check_ext_dependencies(name: str, optional: bool) -> bool:
    """Check if external dependency `name` is found if mandatory.

    Parameters
    ----------
    name : str
        The name of the dependency.
    optional : bool
        Whether the dependency is optional. For external dependencies marked
        as optional, there should be an implementation provided with junfier.

    Returns
    -------
    bool
        Whether the external dependency was found.

    """
    # Check for afni
    if name == "afni":
        found = _check_afni()
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


def _check_afni() -> bool:
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
    if completed_process.returncode == 0:
        return True
    else:
        return False
