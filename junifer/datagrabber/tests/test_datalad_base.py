"""Provide tests for datalad_base."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import Type

import datalad.api as dl
import pytest

from junifer.datagrabber.datalad_base import DataladDataGrabber


_testing_dataset = {
    "example_bids": {
        "uri": "https://gin.g-node.org/juaml/datalad-example-bids",
        "commit": "522dfb203afcd2cd55799bf347f9b211919a7338",
        "id": "fec92475-d9c0-4409-92ba-f041b6a12c40",
    },
    "example_bids_ses": {
        "uri": "https://gin.g-node.org/juaml/datalad-example-bids-ses",
        "commit": "3d08d55d1faad4f12ab64ac9497544a0d924d47a",
        "id": "c83500d0-532f-45be-baf1-0dab703bdc2a",
    },
}


def test_datalad_base_abstractness() -> None:
    """Test datalad base is abstract."""
    with pytest.raises(TypeError, match=r"abstract"):
        DataladDataGrabber()  # type: ignore


@pytest.fixture
def concrete_datagrabber() -> Type[DataladDataGrabber]:
    """Return a concrete datagrabber class.

    Returns
    -------
    DataladDataGrabber
        A concrete datagrabber class.

    """

    class MyDataGrabber(DataladDataGrabber):  # type: ignore
        def __init__(self, datadir, uri):
            super().__init__(
                datadir=datadir,
                rootdir="example_bids",
                uri=uri,
                types=["T1w", "BOLD"],
            )

        def get_item(self, subject):
            out = {
                "T1w": {
                    "path": self.datadir
                    / f"{subject}/anat/{subject}_T1w.nii.gz"
                },
                "BOLD": {
                    "path": self.datadir
                    / f"{subject}/func/{subject}_task-rest_bold.nii.gz"
                },
            }
            return out

        def get_elements(self):
            return [f"sub-{i:02d}" for i in range(1, 10)]

        def get_element_keys(self):
            return ["subject"]

    return MyDataGrabber


def test_datalad_install_errors(
    tmp_path: Path, concrete_datagrabber: Type
) -> None:
    """Test datalad base install errors / warnings.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    concrete_datagrabber : DataladDataGrabber
        A concrete datagrabber class to use.
    """

    # Dataset cloned outside of datagrabber
    datadir = tmp_path / "cloned_uri"
    uri = _testing_dataset["example_bids"]["uri"]
    uri2 = _testing_dataset["example_bids_ses"]["uri"]

    # Files are not there
    assert datadir.exists() is False
    # Clone dataset
    dl.clone(uri, datadir)  # type: ignore
    dg = concrete_datagrabber(datadir=datadir, uri=uri2)
    with pytest.raises(ValueError, match=r"different ID"):
        with dg:
            pass

    elem1_t1w = datadir / "example_bids/sub-01/anat/sub-01_T1w.nii.gz"
    elem1_t1w.unlink()
    with open(elem1_t1w, "w") as f:
        f.write("modified!")

    dg = concrete_datagrabber(datadir=datadir, uri=uri)
    with pytest.warns(RuntimeWarning, match=r"one file is not clean"):
        with dg:
            pass


def test_datalad_clone_cleanup(
    tmp_path: Path, concrete_datagrabber: Type
) -> None:
    """Test datalad base clone and remove.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    concrete_datagrabber : DataladDataGrabber
        A concrete datagrabber class to use.
    """

    # Clone whole dataset
    datadir = tmp_path / "newclone"
    uri = _testing_dataset["example_bids"]["uri"]
    elem1_bold = (
        datadir / "example_bids/sub-01/func/sub-01_task-rest_bold.nii.gz"
    )
    elem1_t1w = datadir / "example_bids/sub-01/anat/sub-01_T1w.nii.gz"

    assert datadir.exists() is False
    assert elem1_bold.is_file() is False
    assert elem1_t1w.is_file() is False
    with concrete_datagrabber(datadir=datadir, uri=uri) as dg:
        assert datadir.exists() is True
        assert dg._was_cloned is True
        assert elem1_bold.is_file() is False
        assert elem1_bold.is_symlink() is True
        assert elem1_t1w.is_file() is False
        assert elem1_t1w.is_symlink() is True
        elem1 = dg["sub-01"]
        assert "meta" in elem1["BOLD"]
        meta = elem1["BOLD"]["meta"]
        assert "datagrabber" in meta
        assert "datalad_dirty" in meta["datagrabber"]
        assert meta["datagrabber"]["datalad_dirty"] is False
        assert hasattr(dg, "_got_files") is False
        assert datadir.exists() is True
        assert elem1_bold.is_file() is True
        assert elem1_bold.is_symlink() is True
        assert elem1_t1w.is_file() is True
        assert elem1_t1w.is_symlink() is True

    assert datadir.exists() is False
    assert len(list(datadir.glob("*"))) == 0


def test_datalad_previously_cloned(
    tmp_path: Path, concrete_datagrabber: Type
) -> None:
    """Test datalad base on cloned dataset.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    concrete_datagrabber : DataladDataGrabber
        A concrete datagrabber class to use.
    """

    # Dataset cloned outside of datagrabber
    datadir = tmp_path / "cloned"
    elem1_bold = (
        datadir / "example_bids/sub-01/func/sub-01_task-rest_bold.nii.gz"
    )
    elem1_t1w = datadir / "example_bids/sub-01/anat/sub-01_T1w.nii.gz"
    uri = _testing_dataset["example_bids"]["uri"]
    commit = _testing_dataset["example_bids"]["commit"]
    remote_id = _testing_dataset["example_bids"]["id"]
    # Files are not there
    assert datadir.exists() is False
    assert elem1_bold.exists() is False
    assert elem1_t1w.exists() is False

    # Clone dataset
    dl.clone(uri, datadir, result_renderer="disabled")  # type: ignore

    # Files are there, but are empty symbolic links
    assert datadir.exists() is True
    assert elem1_bold.is_symlink() is True
    assert elem1_bold.is_file() is False
    assert elem1_t1w.is_symlink() is True
    assert elem1_t1w.is_file() is False
    with concrete_datagrabber(datadir=datadir, uri=uri) as dg:
        assert datadir.exists() is True
        assert dg._was_cloned is False
        elem1 = dg["sub-01"]
        assert "meta" in elem1["BOLD"]
        meta = elem1["BOLD"]["meta"]
        assert "datagrabber" in meta
        assert "datalad_dirty" in meta["datagrabber"]
        assert meta["datagrabber"]["datalad_dirty"] is False
        assert "datalad_commit_id" in meta["datagrabber"]
        assert meta["datagrabber"]["datalad_commit_id"] == commit
        assert "datalad_id" in meta["datagrabber"]
        assert meta["datagrabber"]["datalad_id"] == remote_id

        assert hasattr(dg, "_got_files") is True
        # Files are there and symlinks are fixed
        assert elem1["BOLD"]["path"].is_file() is True
        assert elem1["BOLD"]["path"].is_symlink() is True
        assert elem1["T1w"]["path"].is_file() is True
        assert elem1["T1w"]["path"].is_symlink() is True

        # Datagrabber fetched two files
        assert len(dg._got_files) == 2
        assert any(x.name == "sub-01_T1w.nii.gz" for x in dg._got_files)
        assert any(
            x.name == "sub-01_task-rest_bold.nii.gz" for x in dg._got_files
        )

    assert datadir.exists() is True
    assert len(list(datadir.glob("*"))) > 0


def test_datalad_previously_cloned_and_get(
    tmp_path: Path, concrete_datagrabber: Type
) -> None:
    """Test datalad base on cloned dataset with files present.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    concrete_datagrabber : DataladDataGrabber
        A concrete datagrabber class to use.
    """

    # Dataset cloned outside of datagrabber with some files present
    datadir = tmp_path / "cloned_clean"
    elem1_bold = (
        datadir / "example_bids/sub-01/func/sub-01_task-rest_bold.nii.gz"
    )
    elem1_t1w = datadir / "example_bids/sub-01/anat/sub-01_T1w.nii.gz"
    uri = _testing_dataset["example_bids"]["uri"]
    commit = _testing_dataset["example_bids"]["commit"]
    remote_id = _testing_dataset["example_bids"]["id"]

    # Files are not there
    assert datadir.exists() is False
    assert elem1_bold.exists() is False
    assert elem1_t1w.exists() is False

    # Clone dataset
    dl.clone(uri, datadir, result_renderer="disabled")  # type: ignore

    # Files are there, but are empty symbolic links
    assert datadir.exists() is True
    assert elem1_bold.is_symlink() is True
    assert elem1_bold.is_file() is False
    assert elem1_t1w.is_symlink() is True
    assert elem1_t1w.is_file() is False

    dl.get(  # type: ignore
        elem1_t1w, dataset=datadir, result_renderer="disabled"
    )

    assert elem1_bold.is_symlink() is True
    assert elem1_bold.is_file() is False
    assert elem1_t1w.is_symlink() is True
    assert elem1_t1w.is_file() is True

    with concrete_datagrabber(datadir=datadir, uri=uri) as dg:
        assert datadir.exists() is True
        assert dg._was_cloned is False
        elem1 = dg["sub-01"]
        assert "meta" in elem1["BOLD"]
        meta = elem1["BOLD"]["meta"]
        assert "datagrabber" in meta
        assert "datalad_dirty" in meta["datagrabber"]
        assert meta["datagrabber"]["datalad_dirty"] is False
        assert "datalad_commit_id" in meta["datagrabber"]
        assert meta["datagrabber"]["datalad_commit_id"] == commit
        assert "datalad_id" in meta["datagrabber"]
        assert meta["datagrabber"]["datalad_id"] == remote_id

        assert hasattr(dg, "_got_files") is True
        # Files are there and symlinks are fixed
        assert elem1["BOLD"]["path"].is_file() is True
        assert elem1["BOLD"]["path"].is_symlink() is True
        assert elem1["T1w"]["path"].is_file() is True
        assert elem1["T1w"]["path"].is_symlink() is True

        # Datagrabber fetched two files
        assert len(dg._got_files) == 1
        assert dg._got_files[0].name == "sub-01_task-rest_bold.nii.gz"

    assert datadir.exists() is True
    assert len(list(datadir.glob("*"))) > 0

    # Same state as before using the datagrabber
    assert elem1_bold.is_symlink() is True
    assert elem1_bold.is_file() is False
    assert elem1_t1w.is_symlink() is True
    assert elem1_t1w.is_file() is True


def test_datalad_previously_cloned_and_get_dirty(
    tmp_path: Path, concrete_datagrabber: Type
) -> None:
    """Test datalad base on a dirty cloned dataset.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    concrete_datagrabber : DataladDataGrabber
        A concrete datagrabber class to use.
    """

    # Dataset cloned outside of datagrabber with some files present and dirty
    datadir = tmp_path / "cloned_dirty"
    elem1_bold = (
        datadir / "example_bids/sub-01/func/sub-01_task-rest_bold.nii.gz"
    )
    elem1_t1w = datadir / "example_bids/sub-01/anat/sub-01_T1w.nii.gz"
    uri = _testing_dataset["example_bids"]["uri"]
    commit = _testing_dataset["example_bids"]["commit"]
    remote_id = _testing_dataset["example_bids"]["id"]

    # Files are not there
    assert datadir.exists() is False
    assert elem1_bold.exists() is False
    assert elem1_t1w.exists() is False

    # Clone dataset
    dl.clone(uri, datadir, result_renderer="disabled")  # type: ignore

    # Files are there, but are empty symbolic links
    assert datadir.exists() is True
    assert elem1_bold.is_symlink() is True
    assert elem1_bold.is_file() is False
    assert elem1_t1w.is_symlink() is True
    assert elem1_t1w.is_file() is False

    dl.get(  # type: ignore
        elem1_t1w, dataset=datadir, result_renderer="disabled"
    )

    assert elem1_bold.is_symlink() is True
    assert elem1_bold.is_file() is False
    assert elem1_t1w.is_symlink() is True
    assert elem1_t1w.is_file() is True

    elem1_t1w.unlink()
    with open(elem1_t1w, "w") as f:
        f.write("modified!")

    with concrete_datagrabber(datadir=datadir, uri=uri) as dg:
        assert datadir.exists() is True
        assert dg._was_cloned is False
        elem1 = dg["sub-01"]
        assert "meta" in elem1["BOLD"]
        meta = elem1["BOLD"]["meta"]
        assert "datagrabber" in meta
        assert "datalad_dirty" in meta["datagrabber"]
        assert meta["datagrabber"]["datalad_dirty"] is True
        assert "datalad_commit_id" in meta["datagrabber"]
        assert meta["datagrabber"]["datalad_commit_id"] == commit
        assert "datalad_id" in meta["datagrabber"]
        assert meta["datagrabber"]["datalad_id"] == remote_id

        assert hasattr(dg, "_got_files") is True
        # Files are there and symlinks are fixed
        assert elem1["BOLD"]["path"].is_file() is True
        assert elem1["BOLD"]["path"].is_symlink() is True
        assert elem1["T1w"]["path"].is_file() is True
        assert elem1["T1w"]["path"].is_symlink() is False

        # Datagrabber fetched two files
        assert len(dg._got_files) == 1
        assert dg._got_files[0].name == "sub-01_task-rest_bold.nii.gz"

    # Now get another subject that has not been modified
    with concrete_datagrabber(datadir=datadir, uri=uri) as dg:
        assert datadir.exists() is True
        assert dg._was_cloned is False
        elem2 = dg["sub-02"]
        assert "meta" in elem1["BOLD"]
        meta = elem2["BOLD"]["meta"]
        assert "datagrabber" in meta
        assert "datalad_dirty" in meta["datagrabber"]

        # Dataset is still dirty due to subject sub-01
        assert meta["datagrabber"]["datalad_dirty"] is True

        assert "datalad_commit_id" in meta["datagrabber"]
        assert meta["datagrabber"]["datalad_commit_id"] == commit
        assert "datalad_id" in meta["datagrabber"]
        assert meta["datagrabber"]["datalad_id"] == remote_id

        assert hasattr(dg, "_got_files") is True
        # Files are there and symlinks are fixed
        assert elem2["BOLD"]["path"].is_file() is True
        assert elem2["BOLD"]["path"].is_symlink() is True
        assert elem2["T1w"]["path"].is_file() is True
        assert elem2["T1w"]["path"].is_symlink() is True

        # Datagrabber fetched two files
        assert len(dg._got_files) == 2
        assert any(x.name == "sub-02_T1w.nii.gz" for x in dg._got_files)
        assert any(
            x.name == "sub-02_task-rest_bold.nii.gz" for x in dg._got_files
        )

    assert datadir.exists() is True
    assert len(list(datadir.glob("*"))) > 0

    # Same state as before using the datagrabber
    assert elem1_bold.is_symlink() is True
    assert elem1_bold.is_file() is False
    assert elem1_t1w.is_symlink() is False
    assert elem1_t1w.is_file() is True
