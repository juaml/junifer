"""Provide helper functions for the package."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import subprocess
from typing import List

from .logging import logger, raise_error


def run_ext_cmd(name: str, cmd: List[str]) -> None:
    """Run external command via subprocess.

    Parameters
    ----------
    name : str
        The name of the command.
    cmd : list of str
        The command to run as list of string.

    Raises
    ------
    RuntimeError
        If command fails.

    """
    # Convert list to str
    cmd_str = " ".join(cmd)
    logger.info(f"{name} command to be executed:\n{cmd_str}")
    # Run command via subprocess
    process = subprocess.run(
        cmd_str,  # string needed with shell=True
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True,  # needed for respecting $PATH
        check=False,
    )
    # Check for success or failure
    if process.returncode == 0:
        logger.info(
            f"{name} command succeeded with the following output:\n"
            f"{process.stdout}"
        )
    else:
        raise_error(
            msg=(
                f"{name} command failed with the following error:\n"
                f"{process.stdout}"
            ),
            klass=RuntimeError,
        )
