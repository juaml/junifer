"""Provide tests for functions."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import logging
from pathlib import Path
from typing import List, Union

import pytest

import junifer.testing.registry  # noqa: F401
from junifer.api.functions import collect, queue, run
from junifer.datagrabber.base import BaseDataGrabber
from junifer.pipeline.registry import build


# Define datagrabber
datagrabber = {
    "kind": "OasisVBMTestingDatagrabber",
}

# Define markers
markers = [
    {
        "name": "Schaefer1000x7_Mean",
        "kind": "ParcelAggregation",
        "parcellation": "Schaefer1000x7",
        "method": "mean",
    },
    {
        "name": "Schaefer1000x7_Std",
        "kind": "ParcelAggregation",
        "parcellation": "Schaefer1000x7",
        "method": "std",
    },
]

# Define storage
storage = {
    "kind": "SQLiteFeatureStorage",
}


def test_run_single_element(tmp_path: Path) -> None:
    """Test run function with single element.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    # Create working directory
    workdir = tmp_path / "workdir_single"
    workdir.mkdir()
    # Create output directory
    outdir = tmp_path / "out"
    outdir.mkdir()
    # Create storage
    uri = outdir / "test.db"
    storage["uri"] = uri  # type: ignore
    # Run operations
    run(
        workdir=workdir,
        datagrabber=datagrabber,
        markers=markers,
        storage=storage,
        elements=["sub-01"],
    )
    # Check files
    files = list(outdir.glob("*.db"))
    assert len(files) == 1


def test_run_multi_element(tmp_path: Path) -> None:
    """Test run function with multi element.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    # Create working directory
    workdir = tmp_path / "workdir_multi"
    workdir.mkdir()
    # Create output directory
    outdir = tmp_path / "out"
    outdir.mkdir()
    # Create storage
    uri = outdir / "test.db"
    storage["uri"] = uri  # type: ignore
    # Run operations
    run(
        workdir=workdir,
        datagrabber=datagrabber,
        markers=markers,
        storage=storage,
        elements=["sub-01", "sub-03"],
    )
    # Check files
    files = list(outdir.glob("*.db"))
    assert len(files) == 2


def test_run_and_collect(tmp_path: Path) -> None:
    """Test run and collect functions.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    # Create working directory
    workdir = tmp_path / "workdir"
    workdir.mkdir()
    # Create output directory
    outdir = tmp_path / "out"
    outdir.mkdir()
    # Create storage
    uri = outdir / "test.db"
    storage["uri"] = uri  # type: ignore
    # Run operations
    run(
        workdir=workdir,
        datagrabber=datagrabber,
        markers=markers,
        storage=storage,
    )
    # Get datagrabber
    dg = build(
        step="datagrabber", name=datagrabber["kind"], baseclass=BaseDataGrabber
    )
    elements = dg.get_elements()  # type: ignore
    # This should create 10 files
    files = list(outdir.glob("*.db"))
    assert len(files) == len(elements)
    # But the test.db file should not exist
    assert not uri.exists()
    # Collect in storage
    collect(storage)
    # Now the file exists
    assert uri.exists()


def test_queue_invalid_job_queue(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test queue function for invalid job queue.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    monkeypatch : pytest.MonkeyPatch
        The monkeypatch object.

    """
    with pytest.raises(ValueError, match="Unknown queue kind"):
        with monkeypatch.context() as m:
            m.chdir(tmp_path)
            queue(
                config={"elements": ["sub-001"]},
                kind="ABC",
            )


def test_queue_assets_disallow_overwrite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test overwrite prevention of queue files.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    monkeypatch : pytest.MonkeyPatch
        The monkeypatch object.

    """
    with pytest.raises(ValueError, match="Either delete the directory"):
        with monkeypatch.context() as m:
            m.chdir(tmp_path)
            # First generate assets
            queue(
                config={"elements": ["sub-001"]},
                kind="HTCondor",
                jobname="prevent_overwrite",
            )
            # Re-run to trigger error
            queue(
                config={"elements": ["sub-001"]},
                kind="HTCondor",
                jobname="prevent_overwrite",
            )


def test_queue_assets_allow_overwrite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test overwriting of queue files.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    monkeypatch : pytest.MonkeyPatch
        The monkeypatch object.
    caplog : pytest.LogCaptureFixture
        The logcapturefixture object.

    """
    with monkeypatch.context() as m:
        m.chdir(tmp_path)
        # First generate assets
        queue(
            config={"elements": ["sub-001"]},
            kind="HTCondor",
            jobname="allow_overwrite",
        )
        with caplog.at_level(logging.INFO):
            # Re-run to overwrite
            queue(
                config={"elements": ["sub-001"]},
                kind="HTCondor",
                jobname="allow_overwrite",
                overwrite=True,
            )
            assert "Deleting existing job directory" in caplog.text


@pytest.mark.parametrize(
    "with_",
    [
        "a.py",
        ["a.py"],
        ["a.py", "b"],
    ],
)
def test_queue_with_imports(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    with_: Union[str, List[str]],
) -> None:
    """Test queue with `with` imports.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    monkeypatch : pytest.MonkeyPatch
        The monkeypatch object.
    caplog : pytest.LogCaptureFixture
        The logcapturefixture object.
    with_ : str or list of str
        The parametrized imports.

    """
    with monkeypatch.context() as m:
        m.chdir(tmp_path)
        # Create test file, keeping it simple without conditionals
        (tmp_path / "a.py").touch()
        with caplog.at_level(logging.DEBUG):
            queue(
                config={"with": with_},
                kind="HTCondor",
                elements="sub-001",
            )
            assert "Copying" in caplog.text
            assert "Queue done" in caplog.text


@pytest.mark.parametrize(
    "elements",
    [
        "sub-001",
        ["sub-001"],
        ["sub-001", "sub-002"],
    ],
)
def test_queue_with_elements(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    elements: Union[str, List[str]],
) -> None:
    """Test queue with elements.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    monkeypatch : pytest.MonkeyPatch
        The monkeypatch object.
    caplog : pytest.LogCaptureFixture
        The logcapturefixture object.
    elements : str of list of str
        The parametrized elements for the queue.

    """
    with monkeypatch.context() as m:
        m.chdir(tmp_path)
        with caplog.at_level(logging.INFO):
            queue(
                config={},
                kind="HTCondor",
                elements=elements,
            )
            assert "Queue done" in caplog.text


def test_queue_without_elements(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test queue without elements.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    monkeypatch : pytest.MonkeyPatch
        The monkeypatch object.
    caplog : pytest.LogCaptureFixture
        The logcapturefixture object.

    """
    with monkeypatch.context() as m:
        m.chdir(tmp_path)
        with caplog.at_level(logging.INFO):
            queue(
                config={"datagrabber": datagrabber},
                kind="SLURM",
            )
            assert "Queue done" in caplog.text


def test_queue_condor_invalid_python_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test invalid Python environment check for HTCondor.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    monkeypatch : pytest.MonkeyPatch
        The monkeypatch object.

    """
    with pytest.raises(ValueError, match="Unknown env kind"):
        with monkeypatch.context() as m:
            m.chdir(tmp_path)
            queue(
                config={"elements": "sub-001"},
                kind="HTCondor",
                env={"kind": "galaxy"},
            )


def test_queue_condor_conda_python(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test conda Python environment check for HTCondor.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    monkeypatch : pytest.MonkeyPatch
        The monkeypatch object.
    caplog : pytest.LogCaptureFixture
        The logcapturefixture object.

    """
    with monkeypatch.context() as m:
        m.chdir(tmp_path)
        with caplog.at_level(logging.INFO):
            queue(
                config={"elements": "sub-001"},
                kind="HTCondor",
                jobname="conda_env_check",
                env={"kind": "conda", "name": "conda-env"},
            )
            assert "Copying" in caplog.text
            assert (
                Path(
                    tmp_path
                    / "junifer_jobs"
                    / "conda_env_check"
                    / "run_conda.sh"
                )
                .stat()
                .st_mode
                == 33261
            )


def test_queue_condor_venv_python(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test venv Python environment check for HTCondor.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    monkeypatch : pytest.MonkeyPatch
        The monkeypatch object.
    caplog : pytest.LogCaptureFixture
        The logcapturefixture object.

    """
    with monkeypatch.context() as m:
        m.chdir(tmp_path)
        with caplog.at_level(logging.INFO):
            queue(
                config={"elements": "sub-001"},
                kind="HTCondor",
                env={"kind": "venv", "name": "venv-env"},
            )
            # TODO: needs implementation for testing


@pytest.mark.skip(reason="SLURM not installed on system.")
def test_queue_slurm() -> None:
    """Test job queueing in SLURM."""
    pass
