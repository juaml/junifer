"""Provide tests for datalad_base."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import pytest

from pathlib import Path

import datalad.api as dl

from junifer.datagrabber.datalad_base import DataladDataGrabber


_testing_dataset = {
    "example_bids": {
        "uri": "https://gin.g-node.org/juaml/datalad-example-bids",
        "id": "522dfb203afcd2cd55799bf347f9b211919a7338",
    },
    "example_bids_ses": {
        "uri": "https://gin.g-node.org/juaml/datalad-example-bids-ses",
        "id": "3d08d55d1faad4f12ab64ac9497544a0d924d47a",
    },
}


def test_datalad_base_abstractness() -> None:
    """Test datalad base is abstract."""
    with pytest.raises(TypeError, match=r"abstract"):
        DataladDataGrabber()


def test_datalad_install_errors(tmp_path: Path) -> None:
    """Test datalad base install errors / warnings."""

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

    # Dataset cloned outside of datagrabber
    datadir = tmp_path / "cloned_uri"
    uri = _testing_dataset["example_bids"]["uri"]

    # Files are not there
    assert datadir.exists() is False
    # Clone dataset
    dataset = dl.clone(uri, datadir)  # type: ignore

    dg = MyDataGrabber(datadir=datadir, uri="different")
    with pytest.raises(ValueError, match=r"different URI"):
        with dg:
            pass

    dataset.siblings("add", name="other", url="different")
    dg = MyDataGrabber(datadir=datadir, uri=uri)
    with pytest.warns(RuntimeWarning, match=r"More than one sibling"):
        with dg:
            pass


def test_datalad_selective_cleanup(tmp_path: Path) -> None:
    """Test datalad base cleanup procedure."""

    class MyDataGrabber(DataladDataGrabber):  # type: ignore
        def __init__(self, datadir):
            super().__init__(
                datadir=datadir,
                rootdir="example_bids",
                uri=_testing_dataset["example_bids"]["uri"],
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

    # Clone whole dataset
    datadir = tmp_path / "newclone"
    elem1_bold = (
        datadir / "example_bids/sub-01/func/sub-01_task-rest_bold.nii.gz"
    )
    elem1_t1w = datadir / "example_bids/sub-01/anat/sub-01_T1w.nii.gz"

    assert datadir.exists() is False
    assert elem1_bold.is_file() is False
    assert elem1_t1w.is_file() is False
    with MyDataGrabber(datadir=datadir) as dg:
        assert datadir.exists() is True
        assert dg._was_cloned is True
        assert elem1_bold.is_file() is False
        assert elem1_bold.is_symlink() is True
        assert elem1_t1w.is_file() is False
        assert elem1_t1w.is_symlink() is True
        elem1 = dg["sub-01"]
        assert "meta" in elem1
        assert "datagrabber" in elem1["meta"]
        assert "dataset_dirty" in elem1["meta"]["datagrabber"]
        assert elem1["meta"]["datagrabber"]["dataset_dirty"] is False
        assert hasattr(dg, "_got_files") is False
        assert datadir.exists() is True
        assert elem1_bold.is_file() is True
        assert elem1_bold.is_symlink() is True
        assert elem1_t1w.is_file() is True
        assert elem1_t1w.is_symlink() is True

    assert datadir.exists() is False
    assert len(list(datadir.glob("*"))) == 0

    # Dataset cloned outside of datagrabber
    datadir = tmp_path / "cloned"
    elem1_bold = (
        datadir / "example_bids/sub-01/func/sub-01_task-rest_bold.nii.gz"
    )
    elem1_t1w = datadir / "example_bids/sub-01/anat/sub-01_T1w.nii.gz"
    uri = _testing_dataset["example_bids"]["uri"]

    # Files are not there
    assert datadir.exists() is False
    assert elem1_bold.exists() is False
    assert elem1_t1w.exists() is False

    # Clone dataset
    dl.clone(uri, datadir)  # type: ignore

    # Files are there, but are empty symbolic links
    assert datadir.exists() is True
    assert elem1_bold.is_symlink() is True
    assert elem1_bold.is_file() is False
    assert elem1_t1w.is_symlink() is True
    assert elem1_t1w.is_file() is False
    with MyDataGrabber(datadir=datadir) as dg:
        assert datadir.exists() is True
        assert dg._was_cloned is False
        elem1 = dg["sub-01"]
        assert "meta" in elem1
        assert "datagrabber" in elem1["meta"]
        assert "dataset_dirty" in elem1["meta"]["datagrabber"]
        assert elem1["meta"]["datagrabber"]["dataset_dirty"] is False
        assert hasattr(dg, "_got_files") is True
        # Files are there and symlinks are fixed
        assert elem1["BOLD"]["path"].is_file() is True
        assert elem1["BOLD"]["path"].is_symlink() is True
        assert elem1["T1w"]["path"].is_file() is True
        assert elem1["T1w"]["path"].is_symlink() is True

        # Datagrabber fetched two files
        assert len(dg._got_files) == 2
        assert dg._got_files[0].name == "sub-01_T1w.nii.gz"
        assert dg._got_files[1].name == "sub-01_task-rest_bold.nii.gz"

    assert datadir.exists() is True
    assert len(list(datadir.glob("*"))) > 0

    # Dataset cloned outside of datagrabber with some files present
    datadir = tmp_path / "dirty"
    elem1_bold = (
        datadir / "example_bids/sub-01/func/sub-01_task-rest_bold.nii.gz"
    )
    elem1_t1w = datadir / "example_bids/sub-01/anat/sub-01_T1w.nii.gz"
    uri = _testing_dataset["example_bids"]["uri"]

    # Files are not there
    assert datadir.exists() is False
    assert elem1_bold.exists() is False
    assert elem1_t1w.exists() is False

    # Clone dataset
    dl.clone(uri, datadir)  # type: ignore

    # Files are there, but are empty symbolic links
    assert datadir.exists() is True
    assert elem1_bold.is_symlink() is True
    assert elem1_bold.is_file() is False
    assert elem1_t1w.is_symlink() is True
    assert elem1_t1w.is_file() is False

    dl.get(elem1_t1w, dataset=datadir)  # type: ignore

    assert elem1_bold.is_symlink() is True
    assert elem1_bold.is_file() is False
    assert elem1_t1w.is_symlink() is True
    assert elem1_t1w.is_file() is True

    with MyDataGrabber(datadir=datadir) as dg:
        assert datadir.exists() is True
        assert dg._was_cloned is False
        elem1 = dg["sub-01"]
        assert "meta" in elem1
        assert "datagrabber" in elem1["meta"]
        assert "dataset_dirty" in elem1["meta"]["datagrabber"]
        assert elem1["meta"]["datagrabber"]["dataset_dirty"] is True
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
