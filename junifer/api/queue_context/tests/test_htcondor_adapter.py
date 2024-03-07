"""Provide tests for HTCondorAdapter."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import pytest

from junifer.api.queue_context import HTCondorAdapter


def test_HTCondorAdapter_env_error() -> None:
    """Test error for invalid env kind."""
    with pytest.raises(ValueError, match="Invalid value for `env.kind`"):
        HTCondorAdapter(
            job_name="check_env",
            job_dir=Path("."),
            yaml_config_path=Path("."),
            elements=["sub01"],
            env={"kind": "jambalaya"},
        )


def test_HTCondorAdapter_collect_error() -> None:
    """Test error for invalid collect option."""
    with pytest.raises(ValueError, match="Invalid value for `collect`"):
        HTCondorAdapter(
            job_name="check_collect",
            job_dir=Path("."),
            yaml_config_path=Path("."),
            elements=["sub01"],
            collect="off",
        )


@pytest.mark.parametrize(
    "pre_run, expected_text",
    [
        (None, "# Force datalad"),
        ("# Check this out\n", "# Check this out"),
    ],
)
def test_HTCondorAdapter_pre_run(
    pre_run: Optional[str], expected_text: str
) -> None:
    """Test HTCondorAdapter pre_run().

    Parameters
    ----------
    pre_run : str or None
        The parametrized pre run text.
    expected_text : str
        The parametrized expected text.

    """
    adapter = HTCondorAdapter(
        job_name="test_pre_run",
        job_dir=Path("."),
        yaml_config_path=Path("."),
        elements=["sub01"],
        pre_run=pre_run,
    )
    assert expected_text in adapter.pre_run()


@pytest.mark.parametrize(
    "pre_collect, expected_text, collect",
    [
        (None, "exit 1", "yes"),
        (None, "# This script", "on_success_only"),
        ("# Check this out\n", "# Check this out", "yes"),
        ("# Check this out\n", "# Check this out", "on_success_only"),
    ],
)
def test_HTCondorAdapter_pre_collect(
    pre_collect: Optional[str], expected_text: str, collect: str
) -> None:
    """Test HTCondorAdapter pre_collect().

    Parameters
    ----------
    pre_collect : str or None
        The parametrized pre collect text.
    expected_text : str
        The parametrized expected text.
    collect : str
        The parametrized collect parameter.

    """
    adapter = HTCondorAdapter(
        job_name="test_pre_collect",
        job_dir=Path("."),
        yaml_config_path=Path("."),
        elements=["sub01"],
        pre_collect=pre_collect,
        collect=collect,
    )
    assert expected_text in adapter.pre_collect()


@pytest.mark.parametrize(
    "extra_preamble, expected_text",
    [
        (None, "universe = vanilla"),
        ("# Check this out\n", "# Check this out"),
    ],
)
def test_HTCondorAdapter_run_collect(
    extra_preamble: Optional[str], expected_text: str
) -> None:
    """Test HTCondorAdapter run() and collect().

    Parameters
    ----------
    extra_preamble : str or None
        The parametrized extra preamble text.
    expected_text : str
        The parametrized expected text.

    """
    adapter = HTCondorAdapter(
        job_name="test_run_collect",
        job_dir=Path("."),
        yaml_config_path=Path("."),
        elements=["sub01"],
        extra_preamble=extra_preamble,
    )
    assert expected_text in adapter.run()
    assert expected_text in adapter.collect()


@pytest.mark.parametrize(
    "elements, collect, expected_text",
    [
        (["sub01"], "yes", "FINAL collect"),
        (
            [("sub01", "ses01")],
            "yes",
            "element='sub01,ses01' log_element='sub01-ses01'",
        ),
        (["sub01"], "on_success_only", "JOB collect"),
        (
            [("sub01", "ses01")],
            "on_success_only",
            "element='sub01,ses01' log_element='sub01-ses01'",
        ),
    ],
)
def test_HTCondor_dag(
    elements: List[Union[str, Tuple]], collect: str, expected_text: str
) -> None:
    """Test HTCondorAdapter dag().

    Parameters
    ----------
    elements : list of str or tuple
        The parametrized elements.
    collect : str
       The parametrized collect parameter.
    expected_text : str
        The parametrized expected text.

    """
    adapter = HTCondorAdapter(
        job_name="test_dag",
        job_dir=Path("."),
        yaml_config_path=Path("."),
        elements=elements,
        collect=collect,
    )
    assert expected_text in adapter.dag()


@pytest.mark.parametrize(
    "env",
    [
        {"kind": "conda", "name": "junifer"},
        {"kind": "venv", "name": "./junifer"},
    ],
)
def test_HTCondorAdapter_prepare(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    env: Dict[str, str],
) -> None:
    """Test HTCondorAdapter prepare().

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
            adapter = HTCondorAdapter(
                job_name="test_prepare",
                job_dir=tmp_path,
                yaml_config_path=tmp_path / "config.yaml",
                elements=["sub01"],
                env=env,
            )
            adapter.prepare()

            assert "Creating HTCondor job" in caplog.text
            assert "Creating logs directory" in caplog.text
            assert f"Copying run_{env['kind']}" in caplog.text
            assert "Writing pre_run.sh" in caplog.text
            assert "Writing run_test_prepare.submit" in caplog.text
            assert "Writing pre_collect.sh" in caplog.text
            assert "Writing collect_test_prepare.submit" in caplog.text
            assert "HTCondor job files created" in caplog.text

            assert adapter._exec_path.stat().st_size != 0
            assert adapter._pre_run_path.stat().st_size != 0
            assert adapter._submit_run_path.stat().st_size != 0
            assert adapter._pre_collect_path.stat().st_size != 0
            assert adapter._submit_collect_path.stat().st_size != 0
            assert adapter._dag_path.stat().st_size != 0


def test_HTCondorAdapter_prepare_submit_fail(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test HTCondorAdapter prepare() with failed submit.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    monkeypatch : pytest.MonkeyPatch
        The pytest.MonkeyPatch object.

    """
    with monkeypatch.context() as m:
        m.chdir(tmp_path)
        adapter = HTCondorAdapter(
            job_name="test_prepare_submit_fail",
            job_dir=tmp_path,
            yaml_config_path=tmp_path / "config.yaml",
            elements=["sub01"],
            submit=True,
        )
        with pytest.raises(RuntimeError, match="condor_submit_dag"):
            adapter.prepare()
