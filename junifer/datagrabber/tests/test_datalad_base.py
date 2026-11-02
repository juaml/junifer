"""Provide tests for DataladDataGrabber."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import os
import warnings
from pathlib import Path

import datalad.api as dl
import pytest

from junifer.datagrabber import (
    DataladDataGrabber,
    DataType,
    DataTypeManager,
    register_data_type,
)
from junifer.utils import config


_testing_dataset = {
    "example_bids": {
        "uri": (
            "https://cerebra.fz-juelich.de/junifer/datalad-example-bids.git"
        ),
        "commit": "3f288c8725207ae0c9b3616e093e78cda192b570",
        "id": "582b9696-f13f-42e4-9587-b4e62aa2a8e7",
    },
    "example_bids_ses": {
        "uri": (
            "https://cerebra.fz-juelich.de/junifer/datalad-example-bids-ses.git"
        ),
        "commit": "6b163aa98af76a9eac0272273c27e14127850181",
        "id": "715c17cf-a1b9-42d6-9af8-9f74c1a4a724",
    },
}


@pytest.fixture
def concrete_datagrabber() -> type[DataladDataGrabber]:
    """Return a concrete datalad-based DataGrabber.

    Returns
    -------
    DataladDataGrabber
        A concrete datalad-based DataGrabber.

    """

    class MyDataGrabber(DataladDataGrabber):
        types: list[DataType] = [DataType.T1w, DataType.BOLD]  # noqa: RUF012
        rootdir: Path = Path("example_bids")

        def get_item(self, subject):
            out = {
                "T1w": {
                    "path": self.fulldir
                    / f"{subject}/anat/{subject}_T1w.nii.gz"
                },
                "BOLD": {
                    "path": self.fulldir
                    / f"{subject}/func/{subject}_task-rest_bold.nii.gz"
                },
            }
            return out

        def get_elements(self):
            return [f"sub-{i:02d}" for i in range(1, 10)]

        def get_element_keys(self):
            return ["subject"]

    return MyDataGrabber


def test_DataladDataGrabber_install_errors(
    tmp_path: Path, concrete_datagrabber: type
) -> None:
    """Test DataladDataGrabber install errors / warnings.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    concrete_datagrabber : DataladDataGrabber
        A concrete datalad-based DataGrabber class to use.

    """

    # Dataset cloned outside of datagrabber
    datadir = tmp_path / "cloned_uri"
    uri = _testing_dataset["example_bids"]["uri"]
    uri2 = _testing_dataset["example_bids_ses"]["uri"]

    # Files are not there
    assert datadir.exists() is False
    # Clone dataset
    dl.clone(uri, datadir)
    dg = concrete_datagrabber(datadir=datadir, uri=uri2)
    with pytest.raises(ValueError, match=r"different ID"):
        with dg:
            pass
    # Set config to skip id check and test
    config.set(key="datagrabber.skipidcheck", val=True)
    with dg:
        pass
    # Reset config
    config.delete("datagrabber.skipidcheck")

    elem1_t1w = datadir / "example_bids/sub-01/anat/sub-01_T1w.nii.gz"
    elem1_t1w.unlink()
    with open(elem1_t1w, "w") as f:
        f.write("modified!")

    dg = concrete_datagrabber(datadir=datadir, uri=uri)
    with pytest.warns(RuntimeWarning, match=r"one file is not clean"):
        with dg:
            pass
    # Set config to skip dirty check and test
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        config.set(key="datagrabber.skipdirtycheck", val=True)
        with dg:
            pass
        # Reset config
        config.delete("datagrabber.skipdirtycheck")


def test_DataladDataGrabber_clone_cleanup(
    tmp_path: Path, concrete_datagrabber: type
) -> None:
    """Test DataladDataGrabber clone and remove.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    concrete_datagrabber : DataladDataGrabber
        A concrete datalad-based DataGrabber class to use.

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
        assert datadir.exists() is True
        assert elem1_bold.is_file() is True
        assert elem1_bold.is_symlink() is True
        assert elem1_t1w.is_file() is True
        assert elem1_t1w.is_symlink() is True

    assert datadir.exists() is False
    assert len(list(datadir.glob("*"))) == 0


def test_DataladDataGrabber_clone_create_cleanup(
    concrete_datagrabber: type,
) -> None:
    """Test DataladDataGrabber tempdir clone and remove.

    Parameters
    ----------
    concrete_datagrabber : DataladDataGrabber
        A concrete datalad-based DataGrabber class to use.

    """

    # Clone whole dataset
    uri = _testing_dataset["example_bids"]["uri"]
    with concrete_datagrabber(uri=uri) as dg:
        datadir = dg._repodir
        elem1_bold = (
            datadir / "example_bids/sub-01/func/sub-01_task-rest_bold.nii.gz"
        )
        elem1_t1w = datadir / "example_bids/sub-01/anat/sub-01_T1w.nii.gz"

        assert elem1_bold.is_file() is False
        assert elem1_t1w.is_file() is False
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
        assert datadir.exists() is True
        assert elem1_bold.is_file() is True
        assert elem1_bold.is_symlink() is True
        assert elem1_t1w.is_file() is True
        assert elem1_t1w.is_symlink() is True

    assert datadir.exists() is False
    assert len(list(datadir.glob("*"))) == 0


def test_DataladDataGrabber_previously_cloned(
    tmp_path: Path, concrete_datagrabber: type
) -> None:
    """Test DataladDataGrabber on cloned dataset.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    concrete_datagrabber : DataladDataGrabber
        A concrete datalad-based DataGrabber class to use.

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
    dl.clone(uri, datadir, result_renderer="disabled")

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
        assert elem1["T1w"]["path"].is_symlink() is True

        # Datagrabber fetched two files
        assert len(dg._got_files) == 2
        assert any(x.name == "sub-01_T1w.nii.gz" for x in dg._got_files)
        assert any(
            x.name == "sub-01_task-rest_bold.nii.gz" for x in dg._got_files
        )

    assert datadir.exists() is True
    assert len(list(datadir.glob("*"))) > 0


def test_DataladDataGrabber_previously_cloned_and_get(
    tmp_path: Path, concrete_datagrabber: type
) -> None:
    """Test DataladDataGrabber on cloned dataset with files present.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    concrete_datagrabber : DataladDataGrabber
        A concrete datalad-based DataGrabber class to use.

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
    dl.clone(uri, datadir, result_renderer="disabled")

    # Files are there, but are empty symbolic links
    assert datadir.exists() is True
    assert elem1_bold.is_symlink() is True
    assert elem1_bold.is_file() is False
    assert elem1_t1w.is_symlink() is True
    assert elem1_t1w.is_file() is False

    dl.get(elem1_t1w, dataset=datadir, result_renderer="disabled")

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


def test_DataladDataGrabber_previously_cloned_and_get_dirty(
    tmp_path: Path, concrete_datagrabber: type
) -> None:
    """Test DataladDataGrabber on a dirty cloned dataset.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    concrete_datagrabber : DataladDataGrabber
        A concrete datalad-based DataGrabber class to use.

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
    dl.clone(uri, datadir, result_renderer="disabled")

    # Files are there, but are empty symbolic links
    assert datadir.exists() is True
    assert elem1_bold.is_symlink() is True
    assert elem1_bold.is_file() is False
    assert elem1_t1w.is_symlink() is True
    assert elem1_t1w.is_file() is False

    dl.get(elem1_t1w, dataset=datadir, result_renderer="disabled")

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


def test_DataladDataGrabber_companions_subdatasets(tmp_path: Path) -> None:
    """Test getting the companion files in sub-datasets.

    The files of a sub-dataset are only there once it is installed, by the
    get of the files, so the function giving the companion files must be
    called after it.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    # The state of the dataset when the function is called
    calls = []

    def _header_companions(path: Path) -> list[Path]:
        name = path.read_text().strip().removeprefix("data=")
        companion = path.parent / name
        calls.append(
            {
                "installed": (path.parent / ".datalad").exists(),
                "header": path.read_text(),
                # The link of the companion, without its content
                "companion_link": os.path.lexists(companion),
                "companion_content": companion.exists(),
            }
        )
        return [companion]

    # A sub-dataset for each subject, with a header file naming its data
    # file, as in some EEG formats
    src = tmp_path / "src"
    ds = dl.create(path=src, result_renderer="disabled")
    for subject in ["sub-01", "sub-02"]:
        dl.create(dataset=src, path=src / subject, result_renderer="disabled")
        (src / subject / "rec.hdr").write_text(f"data={subject}_data.bin")
        (src / subject / f"{subject}_data.bin").write_bytes(b"data")
    ds.save(recursive=True, result_renderer="disabled")
    register_data_type(
        name="SubdatasetHeaderData",
        schema={"mandatory": ["pattern"], "optional": {}},
        companions=_header_companions,
    )

    class MyDataGrabber(DataladDataGrabber):
        types: list[DataType] = [  # noqa: RUF012
            DataType("SubdatasetHeaderData")
        ]

        def get_item(self, subject):
            path = self.fulldir / subject / "rec.hdr"
            return {"SubdatasetHeaderData": {"path": path}}

        def get_elements(self):
            return ["sub-01", "sub-02"]

        def get_element_keys(self):
            return ["subject"]

    try:
        with MyDataGrabber(uri=f"file://{src}") as dg:
            # Not installed until the files are got
            assert not (dg.datadir / "sub-01" / ".datalad").exists()
            out = dg["sub-01"]
            # Called once, with the sub-dataset installed and the file got,
            # before getting the companion
            assert calls == [
                {
                    "installed": True,
                    "header": "data=sub-01_data.bin",
                    "companion_link": True,
                    "companion_content": False,
                }
            ]
            path = out["SubdatasetHeaderData"]["path"]
            assert (path.parent / "sub-01_data.bin").read_bytes() == b"data"
            assert not (dg.datadir / "sub-02" / ".datalad").exists()
    finally:
        _ = DataTypeManager().pop("SubdatasetHeaderData")
