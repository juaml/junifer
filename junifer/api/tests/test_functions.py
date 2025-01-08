"""Provide tests for API functions."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import logging
from contextlib import AbstractContextManager, nullcontext
from pathlib import Path
from typing import Any, Optional, Union

import pytest
from nibabel.filebasedimages import ImageFileError
from ruamel.yaml import YAML

import junifer.testing.registry  # noqa: F401
from junifer.api import collect, list_elements, queue, reset, run
from junifer.datagrabber.base import BaseDataGrabber
from junifer.pipeline import PipelineComponentRegistry
from junifer.typing import Elements


# Configure YAML class
yaml = YAML()
yaml.default_flow_style = False
yaml.allow_unicode = True
yaml.indent(mapping=2, sequence=4, offset=2)


# Kept for parametrizing
_datagrabber = {
    "kind": "PartlyCloudyTestingDataGrabber",
}
_bids_ses_datagrabber = {
    "kind": "PatternDataladDataGrabber",
    "uri": "https://gin.g-node.org/juaml/datalad-example-bids-ses",
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
def markers() -> list[dict[str, str]]:
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
        "kind": "SQLiteFeatureStorage",
    }


@pytest.mark.parametrize(
    "datagrabber, element, expect",
    [
        (
            _datagrabber,
            [("sub-01",)],
            pytest.raises(RuntimeError, match="element selectors are invalid"),
        ),
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
        (
            _bids_ses_datagrabber,
            [("sub-01", "ses-100")],
            pytest.raises(RuntimeError, match="element selectors are invalid"),
        ),
        (
            _bids_ses_datagrabber,
            [("sub-100", "ses-01")],
            pytest.raises(RuntimeError, match="element selectors are invalid"),
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
    storage["uri"] = str((tmp_path / "out.sqlite").resolve())
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
        files = list(tmp_path.glob("*.sqlite"))
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
    storage["uri"] = str((tmp_path / "out.sqlite").resolve())
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
    files = list(tmp_path.glob("*.sqlite"))
    assert len(files) == 1


@pytest.mark.parametrize(
    "element, expect",
    [
        (
            [("sub-01",), ("sub-03",)],
            pytest.raises(RuntimeError, match="element selectors are invalid"),
        ),
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
    storage["uri"] = str((tmp_path / "out.sqlite").resolve())
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
        files = list(tmp_path.glob("*.sqlite"))
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
    storage["uri"] = str((tmp_path / "out.sqlite").resolve())
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
    files = list(tmp_path.glob("*.sqlite"))
    assert len(files) == 1
    assert files[0].name == "out.sqlite"


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
    uri = tmp_path / "out.sqlite"
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
        step="datagrabber", name=datagrabber["kind"], baseclass=BaseDataGrabber
    )
    elements = dg.get_elements()  # type: ignore
    # This should create 10 files
    files = list(tmp_path.glob("*.sqlite"))
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
    with_: Union[str, list[str]],
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
    storage["uri"] = tmp_path / "test_reset_run.sqlite"  # type: ignore
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
        storage["uri"] = "test_reset_queue.sqlite"
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
    elements: Optional[list[tuple[str, ...]]],
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
