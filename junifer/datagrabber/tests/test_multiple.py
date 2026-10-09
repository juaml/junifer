"""Provide tests for MultipleDataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import AnyUrl

from junifer.datagrabber import (
    BaseDataGrabber,
    MultipleDataGrabber,
    PatternDataladDataGrabber,
)
from junifer.pipeline import PipelineComponentRegistry


_testing_dataset = {
    "example_bids": {
        "uri": (
            "https://cerebra.fz-juelich.de/junifer/datalad-example-bids.git"
        ),
        "id": "522dfb203afcd2cd55799bf347f9b211919a7338",
    },
    "example_bids_ses": {
        "uri": (
            "https://cerebra.fz-juelich.de/junifer/datalad-example-bids-ses.git"
        ),
        "id": "3d08d55d1faad4f12ab64ac9497544a0d924d47a",
    },
}


def test_MultipleDataGrabber() -> None:
    """Test MultipleDataGrabber."""
    repo_uri = AnyUrl(_testing_dataset["example_bids_ses"]["uri"])
    rootdir = Path("example_bids_ses")
    replacements = ["subject", "session"]

    dg1 = PatternDataladDataGrabber(
        rootdir=rootdir,
        uri=repo_uri,
        types=["T1w", "Warp"],
        patterns={
            "T1w": {
                "pattern": (
                    "{subject}/{session}/anat/{subject}_{session}_T1w.nii.gz"
                ),
                "space": "native",
                "mask": {
                    "pattern": (
                        "{subject}/{session}/anat/{subject}_{session}_"
                        "brain_mask.nii.gz"
                    ),
                    "space": "native",
                },
            },
            "Warp": [
                {
                    "pattern": (
                        "{subject}/{session}/anat/"
                        "{subject}_{session}_from-MNI152NLin2009cAsym_to-T1w_"
                        "xfm.h5"
                    ),
                    "src": "MNI152NLin2009cAsym",
                    "dst": "native",
                    "warper": "ants",
                },
                {
                    "pattern": (
                        "{subject}/{session}/anat/"
                        "{subject}_{session}_from-T1w_to-MNI152NLin2009cAsym_"
                        "xfm.h5"
                    ),
                    "src": "native",
                    "dst": "MNI152NLin2009cAsym",
                    "warper": "ants",
                },
            ],
        },
        replacements=replacements,
    )

    dg2 = PatternDataladDataGrabber(
        rootdir=rootdir,
        uri=repo_uri,
        types="BOLD",
        patterns={
            "BOLD": {
                "pattern": (
                    "{subject}/{session}/func/"
                    "{subject}_{session}_task-rest_bold.nii.gz"
                ),
                "space": "MNI152NLin6Asym",
                "mask": {
                    "pattern": (
                        "{subject}/{session}/func/"
                        "{subject}_{session}_task-rest_brain_mask.nii.gz"
                    ),
                    "space": "MNI152NLin6Asym",
                },
            },
        },
        replacements=replacements,
    )

    dg = MultipleDataGrabber(datagrabbers=[dg1, dg2])

    types = dg.get_types()
    assert "T1w" in types
    assert "Warp" in types
    assert "BOLD" in types

    expected_subs = [
        (f"sub-{i:02d}", f"ses-{j:02d}")
        for j in range(1, 3)
        for i in range(1, 10)
    ]

    with dg:
        subs = list(dg)
        assert set(subs) == set(expected_subs)
        # Check data type
        elem = dg[("sub-01", "ses-01")]
        # Check data types
        assert "T1w" in elem
        assert "Warp" in elem
        assert "BOLD" in elem
        # Check meta
        assert "meta" in elem["BOLD"]
        meta = elem["BOLD"]["meta"]["datagrabber"]
        assert "class" in meta
        assert meta["class"] == "MultipleDataGrabber"
        # Check datagrabbers
        assert "datagrabbers" in meta
        assert len(meta["datagrabbers"]) == 2
        assert meta["datagrabbers"][0]["class"] == "PatternDataladDataGrabber"
        assert meta["datagrabbers"][1]["class"] == "PatternDataladDataGrabber"


def test_MultipleDataGrabber_no_intersection() -> None:
    """Test MultipleDataGrabber without intersection (0 elements)."""
    rootdir = Path("example_bids_ses")
    replacements = ["subject", "session"]

    dg1 = PatternDataladDataGrabber(
        rootdir=rootdir,
        uri=AnyUrl(_testing_dataset["example_bids"]["uri"]),
        types=["T1w", "Warp"],
        patterns={
            "T1w": {
                "pattern": (
                    "{subject}/{session}/anat/{subject}_{session}_T1w.nii.gz"
                ),
                "space": "native",
            },
            "Warp": [
                {
                    "pattern": (
                        "{subject}/{session}/anat/"
                        "{subject}_{session}_from-MNI152NLin2009cAsym_to-T1w_"
                        "xfm.h5"
                    ),
                    "src": "MNI152NLin2009cAsym",
                    "dst": "native",
                    "warper": "ants",
                },
                {
                    "pattern": (
                        "{subject}/{session}/anat/"
                        "{subject}_{session}_from-T1w_to-MNI152NLin2009cAsym_"
                        "xfm.h5"
                    ),
                    "src": "native",
                    "dst": "MNI152NLin2009cAsym",
                    "warper": "ants",
                },
            ],
        },
        replacements=replacements,
    )

    dg2 = PatternDataladDataGrabber(
        rootdir=rootdir,
        uri=AnyUrl(_testing_dataset["example_bids_ses"]["uri"]),
        types="BOLD",
        patterns={
            "BOLD": {
                "pattern": (
                    "{subject}/{session}/func/"
                    "{subject}_{session}_task-rest_bold.nii.gz"
                ),
                "space": "MNI152NLin6Asym",
            },
        },
        replacements=replacements,
    )

    dg = MultipleDataGrabber(datagrabbers=[dg1, dg2])
    expected_subs = set()
    with dg:
        subs = list(dg)
        assert set(subs) == set(expected_subs)


def test_MultipleDataGrabber_get_item() -> None:
    """Test MultipleDataGrabber get_item() error."""
    dg1 = PatternDataladDataGrabber(
        rootdir=Path("example_bids_ses"),
        uri=AnyUrl(_testing_dataset["example_bids"]["uri"]),
        types="T1w",
        patterns={
            "T1w": {
                "pattern": (
                    "{subject}/{session}/anat/{subject}_{session}_T1w.nii.gz"
                ),
                "space": "native",
            },
        },
        replacements=["subject", "session"],
    )

    dg = MultipleDataGrabber(datagrabbers=[dg1])
    with pytest.raises(NotImplementedError):
        dg.get_item(subject="sub-01")


def test_MultipleDataGrabber_validation() -> None:
    """Test MultipleDataGrabber init validation."""
    rootdir = Path("example_bids_ses")

    dg1 = PatternDataladDataGrabber(
        rootdir=rootdir,
        uri=AnyUrl(_testing_dataset["example_bids"]["uri"]),
        types="T1w",
        patterns={
            "T1w": {
                "pattern": (
                    "{subject}/{session}/anat/{subject}_{session}_T1w.nii.gz"
                ),
                "space": "native",
            },
        },
        replacements=["subject", "session"],
    )

    dg2 = PatternDataladDataGrabber(
        rootdir=rootdir,
        uri=AnyUrl(_testing_dataset["example_bids_ses"]["uri"]),
        types="BOLD",
        patterns={
            "BOLD": {
                "pattern": "{subject}/func/{subject}_task-rest_bold.nii.gz",
                "space": "MNI152NLin6Asym",
            },
        },
        replacements=["subject"],
    )

    # Different element keys are joined
    dg = MultipleDataGrabber(datagrabbers=[dg1, dg2])
    assert dg.get_element_keys() == ["subject", "session"]

    with pytest.raises(RuntimeError, match="`T1w` is grabbed by more than"):
        MultipleDataGrabber(datagrabbers=[dg1, dg1])


def test_MultipleDataGrabber_partial_pattern() -> None:
    """Test MultipleDataGrabber partial pattern."""
    repo_uri = AnyUrl(_testing_dataset["example_bids_ses"]["uri"])
    rootdir = Path("example_bids_ses")
    replacements = ["subject", "session"]

    dg1 = PatternDataladDataGrabber(
        rootdir=rootdir,
        uri=repo_uri,
        types="BOLD",
        patterns={
            "BOLD": {
                "pattern": (
                    "{subject}/{session}/func/"
                    "{subject}_{session}_task-rest_bold.nii.gz"
                ),
                "space": "MNI152NLin6Asym",
            },
        },
        replacements=replacements,
    )

    dg2 = PatternDataladDataGrabber(
        rootdir=rootdir,
        uri=repo_uri,
        types="BOLD",
        patterns={
            "BOLD": {
                "confounds": {
                    "pattern": (
                        "{subject}/{session}/func/"
                        "{subject}_{session}_task-rest_"
                        "confounds_regressors.tsv"
                    ),
                    "format": "fmriprep",
                },
            },
        },
        replacements=["subject", "session"],
        partial_pattern_ok=True,
    )

    dg = MultipleDataGrabber(datagrabbers=[dg1, dg2])

    types = dg.get_types()
    assert "BOLD" in types

    expected_subs = [
        (f"sub-{i:02d}", f"ses-{j:02d}")
        for j in range(1, 3)
        for i in range(1, 10)
    ]

    with dg:
        subs = list(dg)
        assert set(subs) == set(expected_subs)
        # Fetch element
        elem = dg[("sub-01", "ses-01")]
        # Check data type and nested data type
        assert "BOLD" in elem
        assert "confounds" in elem["BOLD"]
        # Check meta
        assert "meta" in elem["BOLD"]
        meta = elem["BOLD"]["meta"]["datagrabber"]
        assert "class" in meta
        assert meta["class"] == "MultipleDataGrabber"
        # Check datagrabbers
        assert "datagrabbers" in meta
        assert len(meta["datagrabbers"]) == 2
        assert meta["datagrabbers"][0]["class"] == "PatternDataladDataGrabber"
        assert meta["datagrabbers"][1]["class"] == "PatternDataladDataGrabber"


def _datasets(tmp_path: Path) -> dict[str, Path]:
    """Create local datasets with the data of different datagrabbers.

    * ``fmriprep``: BOLD (with confounds) for ``sub-01`` and ``sub-02``, and
      the ``rest`` and ``movie`` tasks.
    * ``cat``: VBM_GM for ``sub-01``, ``sub-02`` and ``sub-03``.
    * ``confounds``: BOLD confounds for ``sub-01`` and ``sub-02``, and only
      the ``rest`` task.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    Returns
    -------
    dict of str and pathlib.Path
        The paths to the datasets, by name.

    """
    files = [
        f"fmriprep/{s}/func/{s}_task-{t}_{suffix}"
        for s in ("sub-01", "sub-02")
        for t in ("rest", "movie")
        for suffix in ("bold.nii", "desc-confounds.tsv")
    ]
    files += [
        f"cat/{s}/mri/mwp1{s}.nii" for s in ("sub-01", "sub-02", "sub-03")
    ]
    files += [f"confounds/{s}/{s}_task-rest.tsv" for s in ("sub-01", "sub-02")]
    for fname in files:
        (tmp_path / fname).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / fname).touch()
    return {name: tmp_path / name for name in ("fmriprep", "cat", "confounds")}


def _configs(datasets: dict[str, Path]) -> dict[str, dict]:
    """Get the configurations of the datagrabbers of the local datasets.

    Parameters
    ----------
    datasets : dict of str and pathlib.Path
        The paths to the datasets, by name (see ``_datasets``).

    Returns
    -------
    dict of str and dict
        The configurations of the datagrabbers, by dataset name.

    """
    return {
        "fmriprep": {
            "kind": "PatternDataGrabber",
            "datadir": str(datasets["fmriprep"]),
            "types": ["BOLD"],
            "patterns": {
                "BOLD": {
                    "pattern": "{subject}/func/{subject}_task-{task}_bold.nii",
                    "space": "MNI152NLin6Asym",
                    "confounds": {
                        "pattern": (
                            "{subject}/func/{subject}_task-{task}_"
                            "desc-confounds.tsv"
                        ),
                        "format": "fmriprep",
                    },
                },
            },
            "replacements": ["subject", "task"],
        },
        "cat": {
            "kind": "PatternDataGrabber",
            "datadir": str(datasets["cat"]),
            "types": ["VBM_GM"],
            "patterns": {
                "VBM_GM": {
                    "pattern": "{subject}/mri/mwp1{subject}.nii",
                    "space": "MNI152NLin6Asym",
                },
            },
            "replacements": ["subject"],
        },
        "confounds": {
            "kind": "PatternDataGrabber",
            "datadir": str(datasets["confounds"]),
            "types": ["BOLD"],
            "patterns": {
                "BOLD": {
                    "confounds": {
                        "pattern": "{subject}/{subject}_task-{task}.tsv",
                        "format": "fmriprep",
                    },
                },
            },
            "replacements": ["subject", "task"],
            "partial_pattern_ok": True,
        },
    }


def _multiple(tmp_path: Path, names: list[str]) -> MultipleDataGrabber:
    """Get a MultipleDataGrabber with datagrabbers of the local datasets.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    names : list of str
        The names of the datasets of the datagrabbers (see ``_datasets``).

    Returns
    -------
    MultipleDataGrabber
        The datagrabber.

    """
    configs = _configs(_datasets(tmp_path))
    return PipelineComponentRegistry().build_component_instance(
        step="datagrabber",
        name="MultipleDataGrabber",
        baseclass=BaseDataGrabber,
        init_params={
            "datagrabbers": [deepcopy(configs[name]) for name in names]
        },
    )


@pytest.mark.parametrize("names", [["fmriprep", "cat"], ["cat", "fmriprep"]])
def test_MultipleDataGrabber_element_keys(
    tmp_path: Path, names: list[str]
) -> None:
    """Test MultipleDataGrabber with datagrabbers with different element keys.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    names : list of str
        The parametrized datasets of the datagrabbers.

    """
    dg = _multiple(tmp_path, names)
    assert dg.get_element_keys() == ["subject", "task"]
    # sub-03 has no BOLD data
    assert dg.get_elements() == [
        ("sub-01", "movie"),
        ("sub-01", "rest"),
        ("sub-02", "movie"),
        ("sub-02", "rest"),
    ]
    out = dg[("sub-02", "rest")]
    assert out["BOLD"]["path"] == (
        tmp_path / "fmriprep/sub-02/func/sub-02_task-rest_bold.nii"
    )
    assert out["VBM_GM"]["path"] == tmp_path / "cat/sub-02/mri/mwp1sub-02.nii"
    for data_type in ("BOLD", "VBM_GM"):
        assert out[data_type]["meta"]["element"] == {
            "subject": "sub-02",
            "task": "rest",
        }


@pytest.mark.parametrize(
    "names", [["fmriprep", "confounds"], ["confounds", "fmriprep"]]
)
def test_MultipleDataGrabber_nested_types(
    tmp_path: Path, names: list[str]
) -> None:
    """Test MultipleDataGrabber replacing nested data types.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    names : list of str
        The parametrized datasets of the datagrabbers.

    """
    dg = _multiple(tmp_path, names)
    # The confounds dataset only has the rest task
    assert dg.get_elements() == [("sub-01", "rest"), ("sub-02", "rest")]
    out = dg[("sub-01", "rest")]
    # The BOLD image of the first dataset with the confounds of the second
    assert out["BOLD"]["path"] == (
        tmp_path / "fmriprep/sub-01/func/sub-01_task-rest_bold.nii"
    )
    assert out["BOLD"]["confounds"]["path"] == (
        tmp_path / "confounds/sub-01/sub-01_task-rest.tsv"
    )


@pytest.mark.parametrize(
    "names, match",
    [
        (["fmriprep", "fmriprep"], "`BOLD` is grabbed by more than one"),
        (
            ["confounds", "confounds"],
            "`BOLD.confounds` is grabbed by more than one",
        ),
    ],
)
def test_MultipleDataGrabber_overlapping_types(
    tmp_path: Path, names: list[str], match: str
) -> None:
    """Test MultipleDataGrabber errors with overlapping data types.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    names : list of str
        The parametrized datasets of the datagrabbers.
    match : str
        The parametrized error message.

    """
    with pytest.raises(RuntimeError, match=match):
        _multiple(tmp_path, names)


def test_MultipleDataGrabber_three_datasets(tmp_path: Path) -> None:
    """Test MultipleDataGrabber with the data of three datasets.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    dg = _multiple(tmp_path, ["fmriprep", "cat", "confounds"])
    assert dg.get_types() == ["BOLD", "VBM_GM"]
    assert dg.get_elements() == [("sub-01", "rest"), ("sub-02", "rest")]
    out = dg[("sub-02", "rest")]
    assert out["BOLD"]["path"].parent == tmp_path / "fmriprep/sub-02/func"
    assert out["BOLD"]["confounds"]["path"].parent == (
        tmp_path / "confounds/sub-02"
    )
    assert out["VBM_GM"]["path"].parent == tmp_path / "cat/sub-02/mri"
