"""Provide helper functions for the package."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import collections.abc
import subprocess
import sys

from .logging import logger, raise_error


__all__ = ["deep_update", "run_ext_cmd"]


def run_ext_cmd(name: str, cmd: list[str]) -> None:
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
            f"{process.stdout.decode(sys.stdout.encoding)}"
        )
    else:
        raise_error(
            msg=(
                f"{name} command failed with the following error:\n"
                f"{process.stdout.decode(sys.stdout.encoding)}"
            ),
            klass=RuntimeError,
        )


def deep_update(d: dict, u: dict) -> dict:
    """Deep update `d` with `u`.

    From: "https://stackoverflow.com/questions/3232943/update-value-of-a-nested
    -dictionary-of-varying-depth"

    Parameters
    ----------
    d : dict
        The dictionary to deep-update.
    u : dict
        The dictionary to deep-update `d` with.

    Returns
    -------
    dict
        The updated dictionary.

    """
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = deep_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d
