"""Provide tests for GnuParallelLocalAdapter."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

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


@pytest.mark.parametrize(
    "elements, expected_text",
    [
        (["sub01", "sub02"], "sub01\nsub02"),
        ([("sub01", "ses01"), ("sub02", "ses01")], "sub01,ses01\nsub02,ses01"),
    ],
)
def test_GnuParallelLocalAdapter_elements(
    elements: List[Union[str, Tuple]],
    expected_text: str,
) -> None:
    """Test GnuParallelLocalAdapter elements().

    Parameters
    ----------
    elements : list of str or tuple
        The parametrized elements.
    expected_text : str
        The parametrized expected text.

    """
    adapter = GnuParallelLocalAdapter(
        job_name="test_elements",
        job_dir=Path("."),
        yaml_config_path=Path("."),
        elements=elements,
    )
    assert expected_text in adapter.elements()


@pytest.mark.parametrize(
    "pre_run, expected_text",
    [
        (None, "# Force datalad"),
        ("# Check this out\n", "# Check this out"),
    ],
)
def test_GnuParallelLocalAdapter_pre_run(
    pre_run: Optional[str], expected_text: str
) -> None:
    """Test GnuParallelLocalAdapter pre_run().

    Parameters
    ----------
    pre_run : str or None
        The parametrized pre run text.
    expected_text : str
        The parametrized expected text.

    """
    adapter = GnuParallelLocalAdapter(
        job_name="test_pre_run",
        job_dir=Path("."),
        yaml_config_path=Path("."),
        elements=["sub01"],
        pre_run=pre_run,
    )
    assert expected_text in adapter.pre_run()


@pytest.mark.parametrize(
    "pre_collect, expected_text",
    [
        (None, "# This script"),
        ("# Check this out\n", "# Check this out"),
    ],
)
def test_GnuParallelLocalAdapter_pre_collect(
    pre_collect: Optional[str],
    expected_text: str,
) -> None:
    """Test GnuParallelLocalAdapter pre_collect().

    Parameters
    ----------
    pre_collect : str or None
        The parametrized pre collect text.
    expected_text : str
        The parametrized expected text.

    """
    adapter = GnuParallelLocalAdapter(
        job_name="test_pre_collect",
        job_dir=Path("."),
        yaml_config_path=Path("."),
        elements=["sub01"],
        pre_collect=pre_collect,
    )
    assert expected_text in adapter.pre_collect()


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
            assert "Writing pre_run.sh" in caplog.text
            assert "Writing run_test_prepare.sh" in caplog.text
            assert "Writing pre_collect.sh" in caplog.text
            assert "Writing collect_test_prepare.sh" in caplog.text
            assert "Shell scripts created" in caplog.text

            assert adapter._exec_path.stat().st_size != 0
            assert adapter._elements_file_path.stat().st_size != 0
            assert adapter._pre_run_path.stat().st_size != 0
            assert adapter._run_path.stat().st_size != 0
            assert adapter._pre_collect_path.stat().st_size != 0
            assert adapter._collect_path.stat().st_size != 0
