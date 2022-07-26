"""Provide tests for functions."""

import tempfile
from pathlib import Path

from junifer.api.registry import build
from junifer.api.functions import run, collect
from junifer.datagrabber.base import BaseDataGrabber
import junifer.testing.registry  # noqa: F401

datagrabber = {
    'kind': 'OasisVBMTestingDatagrabber',
}

markers = [
    {'name': 'Schaefer1000x7_Mean',
     'kind': 'ParcelAggregation',
     'atlas': 'Schaefer1000x7',
     'method': 'mean'},
    {'name': 'Schaefer1000x7_Std',
     'kind': 'ParcelAggregation',
     'atlas': 'Schaefer1000x7',
     'method': 'std'}
]

storage = {
    'kind': 'SQLiteFeatureStorage',
}


def test_run():
    """Test run function."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        workdir = tmp_path / 'workdir'
        workdir.mkdir()
        outdir = tmp_path / 'out'
        outdir.mkdir()
        uri = outdir / 'test.db'
        storage['uri'] = uri  # type: ignore
        run(
            workdir=workdir,
            datagrabber=datagrabber,
            markers=markers,
            storage=storage,
            elements=['sub-01']
        )

        files = list(outdir.glob('*.db'))
        assert len(files) == 1

        run(
            workdir=workdir.as_posix(),
            datagrabber=datagrabber,
            markers=markers,
            storage=storage,
            elements=['sub-01', 'sub-03']
        )

        files = list(outdir.glob('*.db'))
        assert len(files) == 2


def test_collect():
    """Test run and collect functions."""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        workdir = tmp_path / 'workdir'
        workdir.mkdir()
        outdir = tmp_path / 'out'
        outdir.mkdir()
        uri = outdir / 'test.db'
        storage['uri'] = uri  # type: ignore
        run(
            workdir=workdir,
            datagrabber=datagrabber,
            markers=markers,
            storage=storage,
        )
        dg = build('datagrabber', datagrabber['kind'], BaseDataGrabber)
        elements = dg.get_elements()

        # This should create 10 files
        files = list(outdir.glob('*.db'))
        assert len(files) == len(elements)

        # But the test.db file should not exist
        assert not uri.exists()
        collect(storage)

        # Now the file exists
        assert uri.exists()
