"""Provide tests for filesystem manipulation."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL
import stat
from pathlib import Path

from junifer.utils.fs import make_executable


def test_make_executable(tmp_path: Path) -> None:
    """Test making path executable.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    test_file_path = tmp_path / "make_me_executable.txt"
    test_file_path.write_bytes(b"umm")
    test_file_stat_initial = test_file_path.stat()
    # Check initial file mode
    assert stat.S_IMODE(test_file_stat_initial.st_mode) & stat.S_IEXEC == 0
    # Make the path executable
    make_executable(test_file_path)
    test_file_stat_final = test_file_path.stat()
    # Check final file mode
    assert stat.S_IMODE(test_file_stat_final.st_mode) & stat.S_IEXEC != 0
