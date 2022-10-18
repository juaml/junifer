"""Provide tests for functions."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

import pytest

import junifer.testing.registry  # noqa: F401
from junifer.api.functions import collect, run
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
        "atlas": "Schaefer1000x7",
        "method": "mean",
    },
    {
        "name": "Schaefer1000x7_Std",
        "kind": "ParcelAggregation",
        "atlas": "Schaefer1000x7",
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


@pytest.mark.skip(reason="HTCondor not installed on system.")
def test_queue_condor() -> None:
    """Test job queueing in HTCondor."""
    pass


@pytest.mark.skip(reason="SLURM not installed on system.")
def test_queue_slurm() -> None:
    """Test job queueing in SLURM."""
    pass
