"""Provide tests for WorkDirManager."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import tempfile
from pathlib import Path

from junifer.pipeline import WorkDirManager


def test_workdir_manager_singleton() -> None:
    """Test that WorkDirManager is a singleton."""
    workdir_mgr_1 = WorkDirManager()
    workdir_mgr_2 = WorkDirManager()
    assert id(workdir_mgr_1) == id(workdir_mgr_2)


def test_workdir_manager_auto_workdir() -> None:
    """Test that automatic workdir creation is in temporary directory."""
    workdir_mgr = WorkDirManager()
    assert workdir_mgr.workdir == Path(tempfile.gettempdir()) / "junifer"


def test_workdir_manager_explicit_workdir(tmp_path: Path) -> None:
    """Test that WorkDirManager works correctly with an explicit workdir.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    workdir_mgr = WorkDirManager()
    workdir_mgr.workdir = tmp_path
    assert workdir_mgr.workdir == tmp_path


def test_workdir_manager_get_and_delete_tempdir(tmp_path: Path) -> None:
    """Test getting and deleting temporary directories.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    workdir_mgr = WorkDirManager()
    workdir_mgr.workdir = tmp_path
    # Check no root temporary directory
    assert workdir_mgr.root_tempdir is None

    tempdir = workdir_mgr.get_tempdir()
    # Should create a temporary directory
    assert workdir_mgr.root_tempdir is not None

    workdir_mgr.delete_tempdir(tempdir)
    workdir_mgr._cleanup()
    # Should remove temporary directory
    assert workdir_mgr.root_tempdir is None
