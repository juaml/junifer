"""Provide tests for API functions."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import logging
import sys
import tempfile
from contextlib import AbstractContextManager, nullcontext
from pathlib import Path
from typing import Any

import pytest
from nibabel.filebasedimages import ImageFileError
from ruamel.yaml import YAML

import junifer.testing.registry  # noqa: F401
from junifer.api import collect, list_elements, parse_yaml, queue, reset, run
from junifer.datagrabber import PatternDataGrabber
from junifer.datagrabber.base import BaseDataGrabber
from junifer.pipeline import (
    MarkerCollection,
    PipelineComponentRegistry,
    WorkDirManager,
)
from junifer.typing import Elements


pytestmark = pytest.mark.external


# Configure YAML class
yaml = YAML()
yaml.default_flow_style = False
yaml.allow_unicode = True
yaml.indent(mapping=2, sequence=4, offset=2)


# Kept for parametrizing
_datagrabber = {
    "kind": "PartlyCloudyTestingDataGrabber",
    # Fewer subjects for faster tests
    "n_subjects": 4,
}
_bids_ses_datagrabber = {
    "kind": "PatternDataladDataGrabber",
    "uri": (
        "https://cerebra.fz-juelich.de/junifer/datalad-example-bids-ses.git"
    ),
    "types": ["T1w", "BOLD"],
    "patterns": {
        "T1w": {
            "pattern": (
                "{subject}/{session}/anat/{subject}_{session}_T1w.nii.gz"
            ),
            "space": "MNI152NLin6Asym",
        },
        "BOLD": {
            "pattern": (
                "{subject}/{session}/func/{subject}_{session}_task-rest_bold.nii.gz"
            ),
            "space": "MNI152NLin6Asym",
        },
    },
    "replacements": ["subject", "session"],
    "rootdir": "example_bids_ses",
}


@pytest.fixture
def datagrabber() -> dict[str, str]:
    """Return a datagrabber as a dictionary."""
    return _datagrabber.copy()


@pytest.fixture
def markers() -> list[dict[str, list[str] | str]]:
    """Return markers as a list of dictionary."""
    return [
        {
            "name": "tian-s1-3T_mean",
            "kind": "ParcelAggregation",
            "parcellation": "TianxS1x3TxMNInonlinear2009cAsym",
            "method": "mean",
        },
        {
            "name": "tian-s1-3T_std",
            "kind": "ParcelAggregation",
            "parcellation": "TianxS1x3TxMNInonlinear2009cAsym",
            "method": "std",
        },
    ]


@pytest.fixture
def storage() -> dict[str, str]:
    """Return a storage as a dictionary."""
    return {
        "kind": "HDF5FeatureStorage",
    }


@pytest.mark.parametrize(
    "datagrabber, element, expect",
    [
        # A complete element
        (_datagrabber, [("sub-01",)], nullcontext()),
        (
            _datagrabber,
            ["sub-01"],
            nullcontext(),
        ),
        (
            _bids_ses_datagrabber,
            ["sub-01"],
            pytest.raises(ImageFileError, match="is not a gzip file"),
        ),
        (
            _bids_ses_datagrabber,
            [("sub-01", "ses-01")],
            pytest.raises(ImageFileError, match="is not a gzip file"),
        ),
        # Complete elements without data
        (
            _bids_ses_datagrabber,
            [("sub-01", "ses-100")],
            pytest.raises(RuntimeError, match="Cannot access"),
        ),
        (
            _bids_ses_datagrabber,
            [("sub-100", "ses-01")],
            pytest.raises(RuntimeError, match="Cannot access"),
        ),
    ],
)
def test_run_single_element(
    tmp_path: Path,
    datagrabber: dict[str, Any],
    markers: list[dict[str, str]],
    storage: dict[str, str],
    element: Elements,
    expect: AbstractContextManager,
) -> None:
    """Test run function with single element.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    datagrabber : dict
        Testing datagrabber as dictionary.
    markers : list of dict
        Testing markers as list of dictionary.
    storage : dict
        Testing storage as dictionary.
    element : list of str or tuple
        The parametrized element.
    expect : typing.ContextManager
        The parametrized ContextManager object.

    """
    # Set storage
    storage["uri"] = str((tmp_path / "out.hdf5").resolve())
    # Run operations
    with expect:
        run(
            workdir=tmp_path,
            datagrabber=datagrabber,
            markers=markers,
            storage=storage,
            elements=element,
        )
        # Check files
        files = list(tmp_path.glob("*.hdf5"))
        assert len(files) == 1


def test_run_single_element_with_preprocessing(
    tmp_path: Path,
    markers: list[dict[str, str]],
    storage: dict[str, str],
) -> None:
    """Test run function with single element and pre-processing.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    markers : list of dict
        Testing markers as list of dictionary.
    storage : dict
        Testing storage as dictionary.

    """
    # Set storage
    storage["uri"] = str((tmp_path / "out.hdf5").resolve())
    # Run operations
    run(
        workdir={"path": tmp_path, "cleanup": False},
        datagrabber={
            "kind": "PartlyCloudyTestingDataGrabber",
            "reduce_confounds": False,
        },
        markers=markers,
        storage=storage,
        preprocessors=[
            {
                "kind": "fMRIPrepConfoundRemover",
            }
        ],
        elements=["sub-01"],
    )
    # Check files
    files = list(tmp_path.glob("*.hdf5"))
    assert len(files) == 1


@pytest.mark.parametrize(
    "element, expect",
    [
        ([("sub-01",), ("sub-03",)], nullcontext()),
        (["sub-01", "sub-03"], nullcontext()),
    ],
)
def test_run_multi_element_multi_output(
    tmp_path: Path,
    datagrabber: dict[str, str],
    markers: list[dict[str, str]],
    storage: dict[str, str],
    element: Elements,
    expect: AbstractContextManager,
) -> None:
    """Test run function with multi element and multi output.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    datagrabber : dict
        Testing datagrabber as dictionary.
    markers : list of dict
        Testing markers as list of dictionary.
    storage : dict
        Testing storage as dictionary.
    element : list of str or tuple
        The parametrized element.
    expect : typing.ContextManager
        The parametrized ContextManager object.

    """
    # Set storage
    storage["uri"] = str((tmp_path / "out.hdf5").resolve())
    storage["single_output"] = False  # type: ignore
    # Run operations
    with expect:
        run(
            workdir=tmp_path,
            datagrabber=datagrabber,
            markers=markers,
            storage=storage,
            elements=element,
        )
        # Check files
        files = list(tmp_path.glob("*.hdf5"))
        assert len(files) == 2


def test_run_multi_element_single_output(
    tmp_path: Path,
    datagrabber: dict[str, str],
    markers: list[dict[str, str]],
    storage: dict[str, str],
) -> None:
    """Test run function with multi element and single output.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    datagrabber : dict
        Testing datagrabber as dictionary.
    markers : list of dict
        Testing markers as list of dictionary.
    storage : dict
        Testing storage as dictionary.

    """
    # Set storage
    storage["uri"] = str((tmp_path / "out.hdf5").resolve())
    storage["single_output"] = True  # type: ignore
    # Run operations
    run(
        workdir=tmp_path,
        datagrabber=datagrabber,
        markers=markers,
        storage=storage,
        elements=["sub-01", "sub-03"],
    )
    # Check files
    files = list(tmp_path.glob("*.hdf5"))
    assert len(files) == 1
    assert files[0].name == "out.hdf5"


def test_run_and_collect(
    tmp_path: Path,
    datagrabber: dict[str, str],
    markers: list[dict[str, str]],
    storage: dict[str, str],
) -> None:
    """Test run and collect functions.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    datagrabber : dict
        Testing datagrabber as dictionary.
    markers : list of dict
        Testing markers as list of dictionary.
    storage : dict
        Testing storage as dictionary.

    """
    # Set storage
    uri = tmp_path / "out.hdf5"
    storage["uri"] = str(uri.resolve())
    storage["single_output"] = False  # type: ignore
    # Run operations
    run(
        workdir=tmp_path,
        datagrabber=datagrabber,
        markers=markers,
        storage=storage,
    )
    # Get datagrabber
    dg = PipelineComponentRegistry().build_component_instance(
        step="datagrabber",
        name=datagrabber["kind"],
        baseclass=BaseDataGrabber,
        init_params={k: v for k, v in datagrabber.items() if k != "kind"},
    )
    elements = dg.get_elements()  # type: ignore
    # This should create one file per element
    files = list(tmp_path.glob("*.hdf5"))
    assert len(files) == len(elements)
    # But the test.hdf5 file should not exist
    assert not uri.exists()
    # Collect in storage
    collect(storage)
    # Now the file exists
    assert uri.exists()


def test_queue_correct_yaml_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    datagrabber: dict[str, str],
    markers: list[dict[str, str]],
    storage: dict[str, str],
) -> None:
    """Test proper YAML config generation for queueing.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    monkeypatch : pytest.MonkeyPatch
        The pytest.MonkeyPatch object.
    caplog : pytest.LogCaptureFixture
        The pytest.LogCaptureFixture object.
    datagrabber : dict
        Testing datagrabber as dictionary.
    markers : list of dict
        Testing markers as list of dictionary.
    storage : dict
        Testing storage as dictionary.

    """
    with monkeypatch.context() as m:
        m.chdir(tmp_path)
        with caplog.at_level(logging.INFO):
            queue(
                config={
                    "with": "junifer.testing.registry",
                    "workdir": {
                        "path": str(tmp_path.resolve()),
                        "cleanup": True,
                    },
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
            assert "Creating job directory at" in caplog.text
            assert "Writing YAML config to" in caplog.text
            assert "Queue done" in caplog.text

        generated_config_yaml_path = Path(
            tmp_path / "junifer_jobs" / "yaml_config_gen_check" / "config.yaml"
        )
        yaml_config = yaml.load(generated_config_yaml_path)
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
        The pytest.MonkeyPatch object.

    """
    with pytest.raises(ValueError, match="Invalid value for `kind`"):
        with monkeypatch.context() as m:
            m.chdir(tmp_path)
            queue(
                config={"elements": [("sub-001",)]},
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
        The pytest.MonkeyPatch object.

    """
    with pytest.raises(ValueError, match="Either delete the directory"):
        with monkeypatch.context() as m:
            m.chdir(tmp_path)
            # First generate assets
            queue(
                config={"elements": [("sub-001",)]},
                kind="HTCondor",
                jobname="prevent_overwrite",
            )
            # Re-run to trigger error
            queue(
                config={"elements": [("sub-001",)]},
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
        The pytest.MonkeyPatch object.
    caplog : pytest.LogCaptureFixture
        The pytest.LogCaptureFixture object.

    """
    with monkeypatch.context() as m:
        m.chdir(tmp_path)
        # First generate assets
        queue(
            config={"elements": [("sub-001",)]},
            kind="HTCondor",
            jobname="allow_overwrite",
        )
        with caplog.at_level(logging.INFO):
            # Re-run to overwrite
            queue(
                config={"elements": [("sub-001",)]},
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
    with_: str | list[str],
) -> None:
    """Test queue with `with` imports.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    monkeypatch : pytest.MonkeyPatch
        The pytest.MonkeyPatch object.
    caplog : pytest.LogCaptureFixture
        The pytest.LogCaptureFixture object.
    with_ : str or list of str
        The parametrized imports.

    """
    with monkeypatch.context() as m:
        m.chdir(tmp_path)
        # Create test file, keeping it simple without conditionals
        (tmp_path / "a.py").touch()
        with caplog.at_level(logging.DEBUG):
            queue(
                config={
                    "with": with_,
                    "workdir": {
                        "path": str(tmp_path.resolve()),
                        "cleanup": False,
                    },
                },
                kind="HTCondor",
                jobname="with_import_check",
                elements=[("sub-001",)],
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
        [("sub-001",)],
        [("sub-001",), ("sub-002",)],
        [("sub-001", "ses-001")],
        [("sub-001", "ses-001"), ("sub-001", "ses-002")],
    ],
)
def test_queue_with_elements(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    elements: list[tuple[str, ...]],
) -> None:
    """Test queue with elements.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    monkeypatch : pytest.MonkeyPatch
        The pytest.MonkeyPatch object.
    caplog : pytest.LogCaptureFixture
        The pytest.LogCaptureFixture object.
    elements : list of tuple
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
    datagrabber: dict[str, str],
) -> None:
    """Test queue without elements.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    monkeypatch : pytest.MonkeyPatch
        The pytest.MonkeyPatch object.
    caplog : pytest.LogCaptureFixture
        The pytest.LogCaptureFixture object.
    datagrabber : dict
        Testing datagrabber as dictionary.

    """
    with monkeypatch.context() as m:
        m.chdir(tmp_path)
        with caplog.at_level(logging.INFO):
            queue(
                config={"datagrabber": datagrabber},
                kind="HTCondor",
            )
            assert "Queue done" in caplog.text


def _workdir(tmp_path: Path, as_dict: bool) -> tuple[str | dict, Path]:
    """Get a working directory in the test directory.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    as_dict : bool
        Whether to give the working directory as a dictionary or a path.

    Returns
    -------
    str or dict
        The working directory, as given to the functions.
    pathlib.Path
        The path to the working directory.

    """
    path = tmp_path / "workdir"
    workdir = {"path": str(path), "cleanup": True} if as_dict else str(path)
    return workdir, path


@pytest.mark.parametrize("as_dict", [False, True])
@pytest.mark.parametrize("elements", [None, ["sub-01"]])
def test_queue_workdir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    datagrabber: dict[str, str],
    elements: list[str] | None,
    as_dict: bool,
) -> None:
    """Test queue sets up the working directory.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    monkeypatch : pytest.MonkeyPatch
        The pytest.MonkeyPatch object.
    datagrabber : dict
        Testing datagrabber as dictionary.
    elements : list of str or None
        The parametrized elements to queue. If None, the elements are
        listed using the datagrabber.
    as_dict : bool
        Whether to give the working directory as a dictionary or a path.

    """
    workdir, path = _workdir(tmp_path, as_dict)
    with monkeypatch.context() as m:
        m.chdir(tmp_path)
        queue(
            config={"workdir": workdir, "datagrabber": datagrabber},
            kind="HTCondor",
            elements=elements,
        )
    assert WorkDirManager().workdir == path
    assert path.is_dir()
    # The working directory is written to the job configuration as given
    config = YAML().load(tmp_path / "junifer_jobs/junifer_job/config.yaml")
    assert config["workdir"] == workdir


def test_queue_workdir_cleanup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    datagrabber: dict[str, str],
) -> None:
    """Test queued jobs clean up the working directory.

    Disabling the cleanup only applies to queueing (e.g. to debug it), as
    the jobs would otherwise leave the files of each element.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    monkeypatch : pytest.MonkeyPatch
        The pytest.MonkeyPatch object.
    datagrabber : dict
        Testing datagrabber as dictionary.

    """
    workdir = {"path": str(tmp_path / "workdir"), "cleanup": False}
    with monkeypatch.context() as m:
        m.chdir(tmp_path)
        with pytest.warns(RuntimeWarning, match="will be set to True"):
            queue(
                config={"workdir": workdir, "datagrabber": datagrabber},
                kind="HTCondor",
            )
    # Queueing does not clean up
    assert WorkDirManager()._cleanup_dirs is False
    # The jobs clean up
    config = YAML().load(tmp_path / "junifer_jobs/junifer_job/config.yaml")
    assert config["workdir"]["cleanup"] is True


@pytest.mark.parametrize("as_dict", [False, True])
def test_collect_workdir(tmp_path: Path, as_dict: bool) -> None:
    """Test collect sets up the working directory.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    as_dict : bool
        Whether to give the working directory as a dictionary or a path.

    """
    workdir, path = _workdir(tmp_path, as_dict)
    storage = {"kind": "HDF5FeatureStorage", "uri": str(tmp_path / "out.hdf5")}
    collect(storage, workdir=workdir)
    assert WorkDirManager().workdir == path
    assert path.is_dir()


@pytest.mark.parametrize("as_dict", [False, True])
def test_reset_workdir(tmp_path: Path, as_dict: bool) -> None:
    """Test reset sets up the working directory.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    as_dict : bool
        Whether to give the working directory as a dictionary or a path.

    """
    workdir, path = _workdir(tmp_path, as_dict)
    storage = {"uri": str(tmp_path / "out.hdf5")}
    reset(config={"workdir": workdir, "storage": storage})
    assert WorkDirManager().workdir == path
    assert path.is_dir()


def test_reset_run(
    tmp_path: Path,
    datagrabber: dict[str, str],
    markers: list[dict[str, str]],
    storage: dict[str, str],
) -> None:
    """Test reset function for run.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    datagrabber : dict
        Testing datagrabber as dictionary.
    markers : list of dict
        Testing markers as list of dictionary.
    storage : dict
        Testing storage as dictionary.

    """
    # Create storage
    storage["uri"] = tmp_path / "test_reset_run.hdf5"  # type: ignore
    # Run operation to generate files
    run(
        workdir=tmp_path,
        datagrabber=datagrabber,
        markers=markers,
        storage=storage,
        elements=["sub-01"],
    )
    # Reset operation
    reset(config={"storage": storage})

    assert not Path(storage["uri"]).exists()


@pytest.mark.parametrize(
    "job_name",
    (
        "job",
        None,
    ),
)
def test_reset_queue(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    datagrabber: dict[str, str],
    markers: list[dict[str, str]],
    storage: dict[str, str],
    job_name: str,
) -> None:
    """Test reset function for queue.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    monkeypatch : pytest.MonkeyPatch
        The pytest.MonkeyPatch object.
    datagrabber : dict
        Testing datagrabber as dictionary.
    markers : list of dict
        Testing markers as list of dictionary.
    storage : dict
        Testing storage as dictionary.
    job_name : str
        The parametrized job name.

    """
    with monkeypatch.context() as m:
        m.chdir(tmp_path)
        # Create storage
        storage["uri"] = "test_reset_queue.hdf5"
        # Set job name
        if job_name is None:
            job_name = "junifer_job"
        # Queue operation to generate files
        queue(
            config={
                "with": "junifer.testing.registry",
                "workdir": str(tmp_path.resolve()),
                "datagrabber": datagrabber,
                "markers": markers,
                "storage": storage,
                "env": {
                    "kind": "conda",
                    "name": "junifer",
                },
                "mem": "8G",
            },
            kind="GNUParallelLocal",
            jobname=job_name,
        )
        # Reset operation
        reset(
            config={
                "storage": storage,
                "queue": {"kind": "GNUParallelLocal", "jobname": job_name},
            }
        )

        assert not Path(storage["uri"]).exists()
        assert not (tmp_path / "junifer_jobs" / job_name).exists()


@pytest.mark.parametrize(
    "elements",
    [
        [("sub-01",)],
        None,
    ],
)
def test_list_elements(
    datagrabber: dict[str, str],
    elements: list[tuple[str, ...]] | None,
) -> None:
    """Test elements listing.

    Parameters
    ----------
    datagrabber : dict
        Testing datagrabber as dictionary.
    elements : str of list of str
        The parametrized elements for filtering.

    """
    listed_elements = list_elements(datagrabber, elements)
    assert "sub-01" in listed_elements


@pytest.mark.parametrize("as_dict", [False, True, None])
def test_list_elements_workdir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    datagrabber: dict[str, str],
    as_dict: bool | None,
) -> None:
    """Test elements listing sets up the working directory.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    monkeypatch : pytest.MonkeyPatch
        The pytest.MonkeyPatch object.
    datagrabber : dict
        Testing datagrabber as dictionary.
    as_dict : bool or None
        Whether to give the working directory as a dictionary or a path.
        If None, no working directory is given and the default is used.

    """
    if as_dict is None:
        # The default working directory is in the temporary directory
        monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
        workdir, path = None, tmp_path / "junifer"
    else:
        workdir, path = _workdir(tmp_path, as_dict)
    listed_elements = list_elements(datagrabber, workdir=workdir)
    assert "sub-01" in listed_elements
    assert WorkDirManager().workdir == path
    assert path.is_dir()


def test_parse_yaml_failure() -> None:
    """Test YAML parsing failure."""
    with pytest.raises(ValueError, match="does not exist"):
        parse_yaml("foo.yaml")


def test_parse_yaml_empty_elements_failure(tmp_path: Path) -> None:
    """Test YAML parsing with empty elements failure.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    # Write test file
    fname = tmp_path / "test_parse_yaml_empty_elements_failure.yaml"
    fname.write_text("elements:")
    # Check test file
    with pytest.raises(ValueError, match="elements key was defined"):
        parse_yaml(fname)


def test_parse_yaml_success(tmp_path: Path) -> None:
    """Test YAML parsing success.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    # Write test file
    fname = tmp_path / "test_parse_yaml_success.yaml"
    fname.write_text("foo: bar")
    # Check test file
    contents = parse_yaml(fname)
    assert "foo" in contents
    assert contents["foo"] == "bar"


def test_parse_yaml_success_with_module_autoload(tmp_path: Path) -> None:
    """Test YAML parsing with single module autoload success.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    # Write test file
    fname = tmp_path / "test_parse_yaml_with_single_module_autoload.yaml"
    fname.write_text("foo: bar\nwith: numpy")
    # Check test file
    contents = parse_yaml(fname)
    assert "foo" in contents
    assert contents["foo"] == "bar"
    assert "with" in contents
    assert contents["with"] == ["numpy"]
    assert "numpy" in sys.modules
    assert "junifer.configs.wrong_config" not in sys.modules


def test_parse_yaml_failure_with_multi_module_autoload(tmp_path: Path) -> None:
    """Test YAML parsing with multi module autoload failure.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    # Write test file
    fname = tmp_path / "test_parse_yaml_with_multi_module_autoload.yaml"
    fname.write_text(
        "foo: bar\nwith:\n  - numpy\n  - junifer.testing.wrong_config"
    )
    # Check test file
    with pytest.raises(ImportError, match="wrong_config"):
        parse_yaml(fname)


def test_parse_yaml_with_wrong_path(tmp_path: Path) -> None:
    """Test YAML parsing with wrong paths in with.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    t_tmp_path = tmp_path / "test_relative_with"
    # Write yaml that includes a relative path
    yaml_path = t_tmp_path / "yamls"
    yaml_path.mkdir(exist_ok=True, parents=True)
    yaml_fname = yaml_path / "test_parse_yaml_wrong_path.yaml"

    yaml_fname.write_text("foo: bar\nwith:\n  -  missingt.py\n  - scipy\n")

    # Check test file
    with pytest.raises(ValueError, match="does not exist"):
        parse_yaml(yaml_fname)


def test_parse_yaml_relative_path(tmp_path: Path) -> None:
    """Test YAML parsing with relative paths in with.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    t_tmp_path = tmp_path / "test_relative_with"

    # Write .py to include
    py_path = t_tmp_path / "external"
    py_path.mkdir(exist_ok=True, parents=True)
    py_fname = py_path / "first.py"
    py_fname.write_text("import numpy as np\n")

    # Write yaml that includes a relative path
    yaml_path = t_tmp_path / "yamls"
    yaml_path.mkdir(exist_ok=True, parents=True)
    yaml_fname = yaml_path / "test_parse_yaml_relative_path.yaml"

    yaml_fname.write_text(
        "foo: bar\nwith:\n  - ../external/first.py\n  - scipy\n"
    )

    # Check test file
    parse_yaml(yaml_fname)


def test_parse_yaml_absolute_path(tmp_path: Path) -> None:
    """Test YAML parsing with absolute paths in with.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    t_tmp_path = tmp_path / "test_relative_with"

    # Write .py to include
    py_path = t_tmp_path / "external"
    py_path.mkdir(exist_ok=True, parents=True)
    py_fname = py_path / "first.py"
    py_fname.write_text("import numpy as np\n")

    # Write yaml that includes a relative path
    yaml_path = t_tmp_path / "yamls"
    yaml_path.mkdir(exist_ok=True, parents=True)
    yaml_fname = yaml_path / "test_parse_yaml_relative_path.yaml"

    yaml_fname.write_text(
        f"foo: bar\nwith:\n  - {py_fname.absolute()}\n  - scipy\n"
    )

    # Check test file
    parse_yaml(yaml_fname)


def test_parse_yaml_multi_module_deps(tmp_path: Path) -> None:
    """Test YAML parsing with multi-module import with deps.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    t_tmp_path = tmp_path / "test_with_multi_module"

    # Write .py to include
    py_path = t_tmp_path / "external"
    py_path.mkdir(exist_ok=True, parents=True)
    py_fname_1 = py_path / "first.py"
    py_fname_1.write_text(
        "import numpy as np\nfrom second import hej\n"
        "def junifer_module_deps(): return ['second.py']\n"
    )
    py_fname_2 = py_path / "second.py"
    py_fname_2.write_text("def hej(): print('hej')\n")

    # Write yaml
    yaml_path = t_tmp_path / "yamls"
    yaml_path.mkdir(exist_ok=True, parents=True)
    yaml_fname = yaml_path / "test_parse_yaml_multi_module.yaml"

    yaml_fname.write_text(
        "foo: bar\nwith:\n  - ../external/first.py\n  - scipy\n"
    )

    # Check test file
    parse_yaml(yaml_fname)


def test_parse_storage_uri_relative(tmp_path: Path) -> None:
    """Test YAML parsing with storage and relative URI.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    fname = tmp_path / "test_parse_yaml_with_storage_uri.yaml"
    fname.write_text("foo: bar\nwith: numpy\nstorage:\n  uri: test.db\n")

    contents = parse_yaml(fname)
    assert "foo" in contents
    assert contents["foo"] == "bar"
    assert "storage" in contents
    assert "uri" in contents["storage"]
    assert contents["storage"]["uri"] == str(tmp_path / "test.db")

    fname = tmp_path / "test_parse_yaml_with_storage_uri.yaml"
    fname.write_text(
        "foo: bar\nwith: numpy\nstorage:\n  uri: ../another/test.db\n"
    )

    contents = parse_yaml(fname)
    assert "foo" in contents
    assert contents["foo"] == "bar"
    assert "storage" in contents
    assert "uri" in contents["storage"]
    assert contents["storage"]["uri"] == str(
        (tmp_path / "../another/test.db").resolve()
    )

    fname = tmp_path / "test_parse_yaml_with_storage_uri.yaml"
    fname.write_text(
        "foo: bar\nwith: numpy\nstorage:\n  uri: /absolute/test.db\n"
    )

    contents = parse_yaml(fname)
    assert "foo" in contents
    assert contents["foo"] == "bar"
    assert "storage" in contents
    assert "uri" in contents["storage"]
    assert contents["storage"]["uri"] == "/absolute/test.db"

    # Just to trick coverage
    fname = tmp_path / "test_parse_yaml_with_storage_uri.yaml"
    fname.write_text("foo: bar\nwith: numpy\nstorage:\n  kind: SomeStorage\n")

    contents = parse_yaml(fname)
    assert "foo" in contents
    assert contents["foo"] == "bar"
    assert "storage" in contents


@pytest.mark.parametrize(
    "datadir, expected",
    [
        # Relative to the YAML file
        ("data", "data"),
        ("../other/data", "../other/data"),
        # Absolute
        ("/absolute/data", "/absolute/data"),
    ],
)
def test_parse_yaml_datadir(
    tmp_path: Path, datadir: str, expected: str
) -> None:
    """Test YAML parsing with the data directory of the datagrabber.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    datadir : str
        The parametrized data directory.
    expected : str
        The parametrized data directory, relative to the YAML file.

    """
    fname = tmp_path / "config.yaml"
    yaml.dump(
        {"datagrabber": {"kind": "DG", "datadir": datadir}}, stream=fname
    )
    contents = parse_yaml(fname)
    assert contents["datagrabber"]["datadir"] == str(
        (tmp_path / expected).resolve()
    )


def test_parse_yaml_datadir_multiple(tmp_path: Path) -> None:
    """Test YAML parsing with the data directories of multiple datagrabbers.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    fname = tmp_path / "config.yaml"
    datagrabber = {
        "kind": "MultipleDataGrabber",
        "datagrabbers": [
            {"kind": "DG", "datadir": "data"},
            {"kind": "DG", "datadir": "/absolute/data"},
            {"kind": "DG"},
        ],
    }
    yaml.dump({"datagrabber": datagrabber}, stream=fname)
    contents = parse_yaml(fname)
    datagrabbers = contents["datagrabber"]["datagrabbers"]
    assert datagrabbers[0]["datadir"] == str(tmp_path / "data")
    assert datagrabbers[1]["datadir"] == "/absolute/data"
    assert "datadir" not in datagrabbers[2]


def test_parse_yaml_queue_venv_relative(tmp_path: Path) -> None:
    """Test YAML parsing with relative venv queue.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    fname = tmp_path / "test_parse_yaml_queue_venv_relative.yaml"
    fname.write_text("queue:\n  env:\n    kind: venv\n    name: .venv\n")
    _ = parse_yaml(fname)


@pytest.mark.parametrize(
    "elements, expected, searches",
    [
        # Complete elements, without searching the dataset
        ([("sub-01", "rest")], [("sub-01", "rest")], 0),
        (
            [("sub-01", "rest"), ("sub-02", "movie")],
            [("sub-01", "rest"), ("sub-02", "movie")],
            0,
        ),
        # Partial elements: all the tasks of a subject
        (["sub-01"], [("sub-01", "movie"), ("sub-01", "rest")], 1),
        ([("sub-01",)], [("sub-01", "movie"), ("sub-01", "rest")], 1),
        # Without duplicates
        (
            [("sub-01", "rest"), ("sub-01", "rest")],
            [("sub-01", "rest")],
            0,
        ),
        # ("sub-01", "rest") matches both selectors
        (
            ["sub-01", "rest"],
            [("sub-01", "movie"), ("sub-01", "rest"), ("sub-02", "rest")],
            1,
        ),
    ],
)
def test_run_element_selectors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    markers: list[dict[str, str]],
    elements: Elements,
    expected: list[tuple[str, str]],
    searches: int,
) -> None:
    """Test run function with complete and partial element selectors.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    monkeypatch : pytest.MonkeyPatch
        The pytest.MonkeyPatch object.
    markers : list of dict
        Testing markers as list of dictionary.
    elements : list of str or tuple
        The parametrized element selectors.
    expected : list of tuple of str
        The parametrized elements to compute.
    searches : int
        The parametrized number of searches of the elements of the dataset.

    """
    computed = []
    n_searches = _run_selectors(
        tmp_path, monkeypatch, markers, elements, computed
    )
    assert sorted(computed) == expected
    assert n_searches == searches


def test_run_element_selectors_invalid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    markers: list[dict[str, str]],
) -> None:
    """Test run function with partial selectors matching no element.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    monkeypatch : pytest.MonkeyPatch
        The pytest.MonkeyPatch object.
    markers : list of dict
        Testing markers as list of dictionary.

    """
    computed = []
    with pytest.raises(RuntimeError, match=r"invalid:\n\['sub-03'\]"):
        _run_selectors(
            tmp_path, monkeypatch, markers, ["sub-01", "sub-03"], computed
        )
    # Nothing is computed, not even the elements of the valid selectors
    assert computed == []


def test_run_element_selectors_sizes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    markers: list[dict[str, str]],
) -> None:
    """Test run function with selectors of different numbers of values.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    monkeypatch : pytest.MonkeyPatch
        The pytest.MonkeyPatch object.
    markers : list of dict
        Testing markers as list of dictionary.

    """
    computed = []
    with pytest.raises(ValueError, match="same number of values"):
        _run_selectors(
            tmp_path,
            monkeypatch,
            markers,
            ["sub-01", ("sub-02", "rest")],
            computed,
        )
    assert computed == []


def _run_selectors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    markers: list[dict[str, str]],
    elements: Elements,
    computed: list[tuple[str, str]],
) -> int:
    """Run with element selectors, only recording the elements to compute.

    The dataset has two subjects (``sub-01`` and ``sub-02``) with two tasks
    (``rest`` and ``movie``).

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    monkeypatch : pytest.MonkeyPatch
        The pytest.MonkeyPatch object.
    markers : list of dict
        Testing markers as list of dictionary.
    elements : list of str or tuple
        The element selectors.
    computed : list of tuple of str
        The list to add the computed elements to.

    Returns
    -------
    int
        The number of searches of the elements of the dataset.

    """
    datadir = tmp_path / "data"
    for subject in ("sub-01", "sub-02"):
        (datadir / subject).mkdir(parents=True)
        for task in ("rest", "movie"):
            (datadir / subject / f"{subject}_task-{task}_bold.nii").touch()
    n_searches = 0
    get_elements = PatternDataGrabber.get_elements

    def fit(self: MarkerCollection, input: dict) -> None:
        element = input["BOLD"]["meta"]["element"]
        computed.append((element["subject"], element["task"]))

    def counted_get_elements(self: PatternDataGrabber) -> Elements:
        nonlocal n_searches
        n_searches += 1
        return get_elements(self)

    monkeypatch.setattr(MarkerCollection, "fit", fit)
    monkeypatch.setattr(
        PatternDataGrabber, "get_elements", counted_get_elements
    )
    run(
        workdir=tmp_path / "workdir",
        datagrabber={
            "kind": "PatternDataGrabber",
            "datadir": str(datadir),
            "types": ["BOLD"],
            "patterns": {
                "BOLD": {
                    "pattern": "{subject}/{subject}_task-{task}_bold.nii",
                    "space": "MNI152NLin6Asym",
                },
            },
            "replacements": ["subject", "task"],
        },
        markers=markers,
        storage={
            "kind": "HDF5FeatureStorage",
            "uri": str(tmp_path / "out.hdf5"),
        },
        elements=elements,
    )
    return n_searches
