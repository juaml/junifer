"""Provide tests for functions."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import logging
from pathlib import Path
from typing import List, Tuple, Union

import pytest
import yaml

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
    uri = outdir / "test.sqlite"
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
    files = list(outdir.glob("*.sqlite"))
    assert len(files) == 1


def test_run_single_element_with_preprocessing(tmp_path: Path) -> None:
    """Test run function with single element and pre-processing.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    # Create working directory
    workdir = tmp_path / "workdir_single_with_preprocess"
    workdir.mkdir()
    # Create output directory
    outdir = tmp_path / "out"
    outdir.mkdir()
    # Create storage
    uri = outdir / "test.sqlite"
    storage["uri"] = uri  # type: ignore
    # Run operations
    run(
        workdir=workdir,
        datagrabber={
            "kind": "PartlyCloudyTestingDataGrabber",
            "reduce_confounds": False,
        },
        markers=[
            {
                "name": "Schaefer100x17_mean_FC",
                "kind": "FunctionalConnectivityParcels",
                "parcellation": "Schaefer100x17",
                "agg_method": "mean",
            }
        ],
        storage=storage,
        preprocessor={
            "kind": "fMRIPrepConfoundRemover",
        },
        elements=["sub-001"],
    )
    # Check files
    files = list(outdir.glob("*.sqlite"))
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
    uri = outdir / "test.sqlite"
    storage["uri"] = uri  # type: ignore
    storage["single_output"] = False  # type: ignore
    # Run operations
    run(
        workdir=workdir,
        datagrabber=datagrabber,
        markers=markers,
        storage=storage,
        elements=["sub-01", "sub-03"],
    )
    # Check files
    files = list(outdir.glob("*.sqlite"))
    assert len(files) == 2


def test_run_multi_element_single_output(tmp_path: Path) -> None:
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
    uri = outdir / "test.sqlite"
    storage["uri"] = uri  # type: ignore
    storage["single_output"] = True  # type: ignore
    # Run operations
    run(
        workdir=workdir,
        datagrabber=datagrabber,
        markers=markers,
        storage=storage,
        elements=["sub-01", "sub-03"],
    )
    # Check files
    files = list(outdir.glob("*.sqlite"))
    assert len(files) == 1
    assert files[0].name == "test.sqlite"


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
    uri = outdir / "test.sqlite"
    storage["uri"] = uri  # type: ignore
    storage["single_output"] = False  # type: ignore
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
    files = list(outdir.glob("*.sqlite"))
    assert len(files) == len(elements)
    # But the test.sqlite file should not exist
    assert not uri.exists()
    # Collect in storage
    collect(storage)
    # Now the file exists
    assert uri.exists()


def test_queue_correct_yaml_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test proper YAML config generation for queueing.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    monkeypatch : pytest.MonkeyPatch
        The monkeypatch object.

    """
    with monkeypatch.context() as m:
        m.chdir(tmp_path)
        queue(
            config={
                "with": "junifer.testing.registry",
                "workdir": str(Path(tmp_path).resolve()),
                "datagrabber": datagrabber,
                "markers": markers,
                "storage": storage,
                "env": {
                    "kind": "conda",
                    "name": "junifer",
                },
                "mem": "8G",
            },
            kind="HTCondor",
            jobname="yaml_config_gen_check",
        )

        generated_config_yaml_path = Path(
            tmp_path / "junifer_jobs" / "yaml_config_gen_check" / "config.yaml"
        )
        with open(generated_config_yaml_path, "r") as f:
            yaml_config = yaml.unsafe_load(f)
        # Check for correct YAML config generation
        assert all(
            key in yaml_config.keys()
            for key in [
                "with",
                "workdir",
                "datagrabber",
                "markers",
                "storage",
                "env",
                "mem",
            ]
        )
        assert "queue" not in yaml_config.keys()


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
                jobname="with_import_check",
                elements="sub-001",
            )
            assert "Copying" in caplog.text
            assert "Queue done" in caplog.text

        # Check that file is copied
        assert Path(
            tmp_path / "junifer_jobs" / "with_import_check" / "a.py"
        ).is_file()


@pytest.mark.parametrize(
    "elements",
    [
        "sub-001",
        ["sub-001"],
        ["sub-001", "sub-002"],
        ("sub-001", "ses-001"),
        [("sub-001", "ses-001")],
        [("sub-001", "ses-001"), ("sub-001", "ses-002")],
    ],
)
def test_queue_with_elements(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    elements: Union[str, List[Union[str, Tuple[str]]], Tuple[str]],
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


@pytest.mark.parametrize(
    "elements, env, mem, cpus, disk, collect",
    [
        (
            ["sub-001"],
            {"kind": "conda", "name": "conda-env"},
            "4G",
            4,
            "4G",
            True,
        ),
        (
            ["sub-001"],
            {"kind": "venv", "name": "venv-env"},
            "8G",
            8,
            "8G",
            False,
        ),
        (["sub-001"], {"kind": "local"}, "12G", 12, "12G", True),
    ],
)
def test_queue_condor_assets_generation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    elements: str,
    env: str,
    mem: str,
    cpus: int,
    disk: str,
    collect: bool,
) -> None:
    """Test HTCondor generated assets.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    monkeypatch : pytest.MonkeyPatch
        The monkeypatch object.
    caplog : pytest.LogCaptureFixture
        The logcapturefixture object.
    elements : str
        The parametrized element names.
    env : dict
        The parametrized env names.
    mem : str
        The parametrized memory size.
    cpus : int
        The parametrized CPUs.
    disk : str
        The parametrized disk size.
    collect : bool
        The parametrized collect option.

    """
    jobname = "condor_assets_gen_check"
    with monkeypatch.context() as m:
        m.chdir(tmp_path)
        with caplog.at_level(logging.INFO):
            queue(
                config={"elements": elements},
                kind="HTCondor",
                jobname=jobname,
                env=env,
                mem=mem,
                cpus=cpus,
                disk=disk,
                collect=collect,
            )

            # Check log directory creation
            assert Path(tmp_path / "junifer_jobs" / jobname / "logs").is_dir()

            run_submit_file_path = Path(
                tmp_path / "junifer_jobs" / jobname / f"run_{jobname}.submit"
            )
            # Check junifer run submit file
            assert run_submit_file_path.is_file()
            # Read run submit file to check if resources are correct
            with open(run_submit_file_path, "r") as f:
                for line in f.read().splitlines():
                    if "request_cpus" in line:
                        assert int(line.split("=")[1].strip()) == cpus
                    if "request_memory" in line:
                        assert line.split("=")[1].strip() == mem
                    if "request_disk" in line:
                        assert line.split("=")[1].strip() == disk

            # Check junifer collect submit file
            assert Path(
                tmp_path
                / "junifer_jobs"
                / jobname
                / f"collect_{jobname}.submit"
            ).is_file()

            dag_file_path = Path(
                tmp_path / "junifer_jobs" / jobname / f"{jobname}.dag"
            )
            # Check junifer dag file
            assert dag_file_path.is_file()
            # Read dag file to check if collect job is found
            element_count = 0
            has_collect_job = False
            with open(dag_file_path, "r") as f:
                for line in f.read().splitlines():
                    if "JOB" in line:
                        element_count += 1
                    if "collect" in line:
                        has_collect_job = True

            if collect:
                assert len(elements) == element_count - 1
                assert has_collect_job is True
            else:
                assert len(elements) == element_count
                assert has_collect_job is False

            # Check submit log
            assert (
                "HTCondor job files created, to submit the job, run"
                in caplog.text
            )


def test_queue_condor_extra_preamble(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test HTCondor extra preamble addition.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    monkeypatch : pytest.MonkeyPatch
        The monkeypatch object.

    """
    jobname = "condor_extra_preamble_check"
    extra_preamble = "FOO = BAR"
    with monkeypatch.context() as m:
        m.chdir(tmp_path)
        queue(
            config={"elements": ["sub-001"]},
            kind="HTCondor",
            jobname=jobname,
            extra_preamble=extra_preamble,
        )

        # Check extra preamble in run submit file
        run_submit_file_path = Path(
            tmp_path / "junifer_jobs" / jobname / f"run_{jobname}.submit"
        )
        with open(run_submit_file_path, "r") as f:
            for line in f.read().splitlines():
                if "FOO" in line:
                    assert line.strip() == extra_preamble

        # Check extra preamble in collect submit file
        collect_submit_file_path = Path(
            tmp_path / "junifer_jobs" / jobname / f"collect_{jobname}.submit"
        )
        with open(collect_submit_file_path, "r") as f:
            for line in f.read().splitlines():
                if "FOO" in line:
                    assert line.strip() == extra_preamble


def test_queue_condor_submission_fail(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test HTCondor job submission failure.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    monkeypatch : pytest.MonkeyPatch
        The monkeypatch object.
    caplog : pytest.LogCaptureFixture
        The logcapturefixture object.

    """
    with pytest.raises(
        FileNotFoundError,
        match="No such file or directory: 'condor_submit_dag'",
    ):
        with monkeypatch.context() as m:
            m.chdir(tmp_path)
            with caplog.at_level(logging.INFO):
                queue(
                    config={"elements": ["sub-001"]},
                    kind="HTCondor",
                    jobname="condor_job_submission_fail",
                    submit=True,
                )
            # Check submit log
            assert "Submitting HTCondor job" in caplog.text


@pytest.mark.skip(reason="SLURM not installed on system.")
def test_queue_slurm() -> None:
    """Test job queueing in SLURM."""
    pass
