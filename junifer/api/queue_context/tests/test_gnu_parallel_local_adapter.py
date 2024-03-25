"""Provide tests for GnuParallelLocalAdapter."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import logging
from pathlib import Path
from typing import Dict

import pytest

from junifer.api.queue_context import GnuParallelLocalAdapter


def test_GnuParallelLocalAdapter_env_error() -> None:
    """Test error for invalid env kind."""
    with pytest.raises(ValueError, match="Invalid value for `env.kind`"):
        GnuParallelLocalAdapter(
            job_name="check_env",
            job_dir=Path("."),
            yaml_config_path=Path("."),
            elements=["sub01"],
            env={"kind": "jambalaya"},
        )


def test_GnuParallelLocalAdapter_run() -> None:
    """Test HTCondorAdapter run()."""
    adapter = GnuParallelLocalAdapter(
        job_name="test_run",
        job_dir=Path("."),
        yaml_config_path=Path("."),
        elements=["sub01"],
    )
    assert "run" in adapter.run()


def test_GnuParallelLocalAdapter_collect() -> None:
    """Test HTCondorAdapter collect()."""
    adapter = GnuParallelLocalAdapter(
        job_name="test_run_collect",
        job_dir=Path("."),
        yaml_config_path=Path("."),
        elements=["sub01"],
    )
    assert "collect" in adapter.collect()


@pytest.mark.parametrize(
    "env",
    [
        {"kind": "conda", "name": "junifer"},
        {"kind": "venv", "name": "./junifer"},
    ],
)
def test_GnuParallelLocalAdapter_prepare(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    env: Dict[str, str],
) -> None:
    """Test GnuParallelLocalAdapter prepare().

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    monkeypatch : pytest.MonkeyPatch
        The pytest.MonkeyPatch object.
    caplog : pytest.LogCaptureFixture
        The pytest.LogCaptureFixture object.
    env : dict
        The parametrized Python environment config.

    """
    with monkeypatch.context() as m:
        m.chdir(tmp_path)
        with caplog.at_level(logging.DEBUG):
            adapter = GnuParallelLocalAdapter(
                job_name="test_prepare",
                job_dir=tmp_path,
                yaml_config_path=tmp_path / "config.yaml",
                elements=["sub01"],
                env=env,
            )
            adapter.prepare()

            assert "GNU parallel" in caplog.text
            assert f"Copying run_{env['kind']}" in caplog.text
            assert "`junifer run`" in caplog.text
            assert "`junifer collect`" in caplog.text

            assert adapter._exec_path.stat().st_size != 0
