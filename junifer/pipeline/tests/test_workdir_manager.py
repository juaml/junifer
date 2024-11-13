"""Provide tests for WorkDirManager."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

from junifer.pipeline import WorkDirManager


def test_workdir_manager_singleton() -> None:
    """Test that WorkDirManager is a singleton."""
    workdir_mgr_1 = WorkDirManager()
    workdir_mgr_2 = WorkDirManager()
    assert id(workdir_mgr_1) == id(workdir_mgr_2)


def test_workdir_manager_workdir(tmp_path: Path) -> None:
    """Test WorkDirManager correctly sets workdir.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    workdir_mgr = WorkDirManager()
    workdir_mgr.workdir = tmp_path
    assert workdir_mgr.workdir == tmp_path


def test_workdir_manager_get_and_delete_element_tempdir(
    tmp_path: Path,
) -> None:
    """Test WorkDirManager gets and deletes element tempdirs correctly.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    workdir_mgr = WorkDirManager()
    workdir_mgr.workdir = tmp_path
    # Check no element directory
    assert workdir_mgr.elementdir is None

    element_tempdir = workdir_mgr.get_element_tempdir()
    # Should create a temporary directory
    assert workdir_mgr.elementdir is not None

    workdir_mgr.delete_element_tempdir(element_tempdir)
    workdir_mgr._cleanup()
    # Should remove temporary directory
    assert workdir_mgr.elementdir is None


def test_workdir_manager_cleanup_elementdir(
    tmp_path: Path,
) -> None:
    """Test WorkDirManager cleans up element directory correctly.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    workdir_mgr = WorkDirManager()
    workdir_mgr.workdir = tmp_path
    # Check no element directory
    assert workdir_mgr.elementdir is None

    workdir_mgr.get_element_tempdir()
    # Should create a temporary directory
    assert workdir_mgr.elementdir is not None

    workdir_mgr.cleanup_elementdir()
    # Should remove temporary directory
    assert workdir_mgr.elementdir is None


def test_workdir_manager_get_and_delete_tempdir(tmp_path: Path) -> None:
    """Test WorkDirManager gets and deletes temporary directories correctly.

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


def test_workdir_manager_no_cleanup(tmp_path: Path) -> None:
    """Test WorkDirManager correctly bypasses cleanup.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    workdir_mgr = WorkDirManager(cleanup=False)
    workdir_mgr.workdir = tmp_path
    # Check no root temporary directory
    assert workdir_mgr.root_tempdir is None

    tempdir = workdir_mgr.get_tempdir()
    assert tempdir.exists()
    # Should create a temporary directory
    assert workdir_mgr.root_tempdir is not None

    workdir_mgr.delete_tempdir(tempdir)
    workdir_mgr._cleanup()

    # Should remove temporary directory
    assert workdir_mgr.root_tempdir is None
    # But the temporary directory should still exist
    assert tempdir.exists()

    # Now the same but for the element directory

    # Check no element directory
    assert workdir_mgr.elementdir is None

    tempdir = workdir_mgr.get_element_tempdir()
    # Should create a temporary directory
    assert workdir_mgr.elementdir is not None

    workdir_mgr.cleanup_elementdir()
    # Should remove temporary directory
    assert workdir_mgr.elementdir is None
    # But the temporary directory should still exist
    assert tempdir.exists()
