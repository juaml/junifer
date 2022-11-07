"""Provide functions for filesystem manipulation."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import stat
from pathlib import Path


def make_executable(path: Path) -> None:
    """Make ``path`` executable.

    Parameters
    ----------
    path : pathlib.Path
        The path to make executable.

    """
    st = path.stat()
    path.chmod(mode=st.st_mode | stat.S_IEXEC)
