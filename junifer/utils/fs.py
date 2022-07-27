"""Provide functions for filesystem."""

import os
import stat


def make_executable(path):
    """Make executable."""
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IEXEC)
