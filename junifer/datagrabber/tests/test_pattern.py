"""Provide tests for PatternDataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from copy import deepcopy
from enum import StrEnum
from itertools import product
from pathlib import Path
from typing import ClassVar

import pytest

from junifer.datagrabber import (
    ConfoundsFormat,
    PatternDataGrabber,
    register_confounds_format,
)


def test_register_confounds_format() -> None:
    """Test confounds format registration."""

    register_confounds_format(
        name="Confounds",
        alias="confounds",
    )
    assert "confounds" in list(ConfoundsFormat)


def test_PatternDataGrabber_errors(tmp_path: Path) -> None:
    """Test PatternDataGrabber errors.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    tmpdir = tmp_path / "pattern_dg_test_errors"

    datagrabber_no_access = PatternDataGrabber(
        datadir=tmpdir,
        types=["BOLD", "T1w"],
        patterns={
            "BOLD": {
                "pattern": "func/{subject}_single.nii",
                "space": "MNI152NLin6Asym",
            },
            "T1w": {
                "pattern": "anat/{subject}_{session}_ses.nii",
                "space": "MNI152NLin6Asym",
            },
        },
        replacements=["subject", "session"],
    )

    with pytest.raises(ValueError, match="element keys must be"):
        datagrabber_no_access[("sub001")]

    # This should not work, file does not exists
    with pytest.raises(RuntimeError, match="Cannot access"):
        datagrabber_no_access[("sub001", "ses001")]

    # Create directories and files
    (tmpdir / "func").mkdir(exist_ok=True, parents=True)
    (tmpdir / "anat").mkdir(exist_ok=True, parents=True)
    for t_subject, t_session in product(range(3), range(2)):
        subject = f"sub{t_subject:03d}"
        session = f"ses{t_session:03d}"
        (tmpdir / "func" / f"{subject}_single.nii").touch()
        if t_subject == 2:
            (tmpdir / "func" / f"{subject}_extra.nii").touch()
        (tmpdir / "anat" / f"{subject}_{session}_ses.nii").touch()

    # This should work, file now exists
    datagrabber_no_access[("sub001", "ses001")]

    datagrabber_multi_access = PatternDataGrabber(
        datadir=tmpdir,
        types=["BOLD", "T1w"],
        patterns={
            "BOLD": {
                "pattern": "func/{subject}_*.nii",
                "space": "MNI152NLin6Asym",
            },
            "T1w": {
                "pattern": "anat/{subject}_{session}_*.nii",
                "space": "MNI152NLin6Asym",
            },
        },
        replacements=["subject", "session"],
    )

    # Access a subject with a missing session
    with pytest.raises(RuntimeError, match="No file matches"):
        datagrabber_multi_access[("sub001", "ses004")]

    # Access a subject with two matching files
    with pytest.raises(RuntimeError, match="More than one"):
        datagrabber_multi_access[("sub002", "ses001")]

    # Access the right one
    datagrabber_multi_access[("sub001", "ses001")]

    datagrabber_fake_access = PatternDataGrabber(
        datadir=tmpdir,
        types=["BOLD", "T1w"],
        patterns={
            "BOLD": {
                "pattern": "func/{subject}_single.nii",
                "space": "MNI152NLin6Asym",
            },
            "T1w": {
                "pattern": "anat2/{subject}_{session}_ses.nii",
                "space": "MNI152NLin6Asym",
            },
        },
        replacements=["subject", "session"],
    )
    assert len(datagrabber_fake_access.get_elements()) == 0


def test_PatternDataGrabber(tmp_path: Path) -> None:
    """Test PatternDataGrabber.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """

    datagrabber_first = PatternDataGrabber(
        datadir=Path("/tmp/data"),
        types=["BOLD", "T1w"],
        patterns={
            "BOLD": {
                "pattern": "func/{subject}.nii",
                "space": "MNI152NLin6Asym",
            },
            "T1w": {
                "pattern": "anat/{subject}.nii",
                "space": "native",
            },
        },
        replacements=["subject"],
    )
    assert datagrabber_first.datadir == Path("/tmp/data")
    assert set(datagrabber_first.types) == {"T1w", "BOLD"}
    assert datagrabber_first.replacements == ["subject"]

    datagrabber_second = PatternDataGrabber(
        datadir=Path("/tmp/data"),
        types=["BOLD", "T1w"],
        patterns={
            "BOLD": {
                "pattern": "func/{subject}.nii",
                "space": "MNI152NLin6Asym",
            },
            "T1w": {
                "pattern": "anat/{subject}_{session}.nii",
                "space": "native",
            },
        },
        replacements=["subject", "session"],
    )
    assert datagrabber_second.datadir == Path("/tmp/data")
    assert set(datagrabber_second.types) == {"T1w", "BOLD"}
    assert datagrabber_second.replacements == ["subject", "session"]

    # Create directories and files
    tmpdir = tmp_path / "pattern_dg_test"
    (tmpdir / "func").mkdir(exist_ok=True, parents=True)
    (tmpdir / "anat").mkdir(exist_ok=True, parents=True)
    (tmpdir / "vbm").mkdir(exist_ok=True, parents=True)
    for t_subject, t_session, t_task in product(
        range(3), range(2), range(2, 4)
    ):
        subject = f"sub{t_subject:03d}"
        session = f"ses{t_session:03d}"
        task = f"task{t_task:03d}"
        if t_subject != 2:
            (tmpdir / "func" / f"{subject}.nii").touch()
        (tmpdir / "anat" / f"{subject}_{session}.nii").touch()
        (tmpdir / "vbm" / f"{subject}_{task}_{session}.nii").touch()

    expected_elements = [
        ("sub000", "ses000"),
        ("sub000", "ses001"),
        ("sub001", "ses000"),
        ("sub001", "ses001"),
        ("sub002", "ses000"),
        ("sub002", "ses001"),
    ]

    datagrabber_third = PatternDataGrabber(
        datadir=tmpdir,
        types="T1w",
        patterns={
            "T1w": {
                "pattern": "anat/{subject}_{session}.nii",
                "space": "native",
            },
        },
        replacements=["subject", "session"],
    )

    elements = datagrabber_third.get_elements()
    assert set(elements) == set(expected_elements)

    expected_elements = [
        ("sub000", "ses000", "task002"),
        ("sub000", "ses000", "task003"),
        ("sub000", "ses001", "task002"),
        ("sub000", "ses001", "task003"),
        ("sub001", "ses000", "task002"),
        ("sub001", "ses000", "task003"),
        ("sub001", "ses001", "task002"),
        ("sub001", "ses001", "task003"),
    ]

    datagrabber_fourth = PatternDataGrabber(
        datadir=tmpdir,
        types=["T1w", "BOLD", "VBM_GM"],
        patterns={
            "BOLD": {
                "pattern": "func/{subject}.nii",
                "space": "MNI152NLin6Asym",
            },
            "T1w": {
                "pattern": "anat/{subject}_{session}.nii",
                "space": "native",
            },
            "VBM_GM": {
                "pattern": "vbm/{subject}_{task}_{session}.nii",
                "space": "MNI152NLin6Asym",
            },
        },
        replacements=["subject", "session", "task"],
    )

    elements = datagrabber_fourth.get_elements()
    assert set(elements) == set(expected_elements)

    out1 = datagrabber_fourth[("sub000", "ses000", "task002")]
    out2 = datagrabber_fourth[("sub000", "ses000", "task003")]

    assert out1["BOLD"]["path"] == out2["BOLD"]["path"]
    assert out1["T1w"]["path"] == out2["T1w"]["path"]
    assert out1["VBM_GM"]["path"] != out2["VBM_GM"]["path"]


def test_PatternDataGrabber_unix_path_expansion(tmp_path: Path) -> None:
    """Test PatterDataGrabber for patterns with unix path expansion.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    # Create test data root dir
    freesurfer_dir = tmp_path / "derivatives" / "freesurfer"
    freesurfer_dir.mkdir(parents=True, exist_ok=True)
    # Create test data sub dirs and files
    for dir_name in ["fsaverage", "sub-0001"]:
        mri_dir = freesurfer_dir / dir_name / "mri"
        mri_dir.mkdir(parents=True, exist_ok=True)
        # Create files
        (mri_dir / "T1.mgz").touch(exist_ok=True)
        (mri_dir / "aseg.mgz").touch(exist_ok=True)
    # Create datagrabber
    dg = PatternDataGrabber(
        datadir=tmp_path,
        types="FreeSurfer",
        patterns={
            "FreeSurfer": {
                "pattern": "derivatives/freesurfer/[!f]{subject}/mri/T1.mg[z]",
                "aseg": {
                    "pattern": (
                        "derivatives/freesurfer/[!f]{subject}/mri/aseg.mg[z]"
                    )
                },
            },
        },
        replacements=["subject"],
    )
    # Check that "fsaverage" is filtered
    elements = dg.get_elements()
    assert elements == ["sub-0001"]
    # Fetch data
    out = dg["sub-0001"]
    # Check paths are found
    assert set(out["FreeSurfer"].keys()) == {"path", "aseg", "meta"}
    assert list(out["FreeSurfer"]["aseg"].keys()) == ["path"]


def test_PatternDataGrabber_get_elements_order(tmp_path: Path) -> None:
    """Test PatternDataGrabber elements with types of different specificity.

    The elements must not depend on the order of the types.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    (tmp_path / "anat").mkdir()
    (tmp_path / "func").mkdir()
    (tmp_path / "func" / "sub-01.nii").touch()
    for ses in ("ses-1", "ses-2"):
        (tmp_path / "anat" / f"sub-01_{ses}.nii").touch()

    dg = PatternDataGrabber(
        datadir=tmp_path,
        # Most specific type first
        types=["T1w", "BOLD"],
        patterns={
            "T1w": {
                "pattern": "anat/{subject}_{session}.nii",
                "space": "native",
            },
            "BOLD": {
                "pattern": "func/{subject}.nii",
                "space": "MNI152NLin6Asym",
            },
        },
        replacements=["subject", "session"],
    )
    assert set(dg.get_elements()) == {
        ("sub-01", "ses-1"),
        ("sub-01", "ses-2"),
    }


@pytest.mark.parametrize("missing", ["func", "anat"])
def test_PatternDataGrabber_get_elements_intersection(
    tmp_path: Path, missing: str
) -> None:
    """Test PatternDataGrabber elements are available for all the types.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    missing : str
        The parametrized directory missing the file for one element.

    """
    (tmp_path / "anat").mkdir()
    (tmp_path / "func").mkdir()
    for subject in ("sub-01", "sub-02"):
        for folder in ("func", "anat"):
            # One element is missing one of the types
            if subject == "sub-02" and folder == missing:
                continue
            (tmp_path / folder / f"{subject}_ses-1.nii").touch()

    dg = PatternDataGrabber(
        datadir=tmp_path,
        types=["BOLD", "T1w"],
        patterns={
            "BOLD": {
                "pattern": "func/{subject}_{session}.nii",
                "space": "MNI152NLin6Asym",
            },
            "T1w": {
                "pattern": "anat/{subject}_{session}.nii",
                "space": "native",
            },
        },
        replacements=["subject", "session"],
    )
    assert dg.get_elements() == [("sub-01", "ses-1")]


# Patterns of the anatomical and functional data (see `_anat_func_files`)
_PATTERNS = {
    "BOLD": {
        "pattern": (
            "{subject}/{session}/func/{subject}_{session}_task-{task}_bold.nii"
        ),
        "space": "MNI152NLin6Asym",
    },
    "VBM_GM": {
        "pattern": "{subject}/anat/{subject}_GM.nii",
        "space": "native",
    },
}


def _anat_func_files(tmp_path: Path) -> None:
    """Create the files of the anatomical and functional data.

    The BOLD data is available for two subjects, two sessions and two tasks,
    and the VBM data (one per subject) for three subjects.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    for subject in ("sub-01", "sub-02", "sub-03"):
        (tmp_path / subject / "anat").mkdir(parents=True)
        (tmp_path / subject / "anat" / f"{subject}_GM.nii").touch()
        if subject == "sub-03":
            continue
        for session in ("ses-1", "ses-2"):
            for task in ("rest", "movie"):
                func = tmp_path / subject / session / "func"
                func.mkdir(parents=True, exist_ok=True)
                (func / f"{subject}_{session}_task-{task}_bold.nii").touch()


def _anat_func_datagrabber(
    tmp_path: Path,
    types: list[str],
    replacements: list[str] | dict | None = None,
) -> PatternDataGrabber:
    """Get a datagrabber with anatomical and functional data.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    types : list of str
        The data types to grab.
    replacements : list of str or dict or None, optional
        The replacements. If None, ``["subject", "session", "task"]``
        (default None).

    Returns
    -------
    PatternDataGrabber
        The datagrabber.

    """
    _anat_func_files(tmp_path)
    return PatternDataGrabber(
        datadir=tmp_path,
        types=types,
        patterns=deepcopy(_PATTERNS),
        replacements=replacements or ["subject", "session", "task"],
    )


def test_PatternDataGrabber_elements_only_anat(tmp_path: Path) -> None:
    """Test PatternDataGrabber elements of data types without all replacements.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    dg = _anat_func_datagrabber(tmp_path, types=["VBM_GM"])
    assert dg.get_element_keys() == ["subject"]
    assert dg.get_elements() == ["sub-01", "sub-02", "sub-03"]
    assert list(dg.filter(["sub-02"])) == ["sub-02"]
    out = dg["sub-02"]
    assert out["VBM_GM"]["path"].name == "sub-02_GM.nii"
    assert out["VBM_GM"]["meta"]["element"] == {"subject": "sub-02"}
    # The elements must have the element keys only
    with pytest.raises(
        ValueError, match=r"element keys must be \['subject'\]"
    ):
        dg.get_item(subject="sub-02", task="rest")


@pytest.mark.parametrize("types", [["BOLD"], ["BOLD", "VBM_GM"]])
def test_PatternDataGrabber_elements_func(
    tmp_path: Path, types: list[str]
) -> None:
    """Test PatternDataGrabber elements of data types with all replacements.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    types : list of str
        The parametrized data types.

    """
    dg = _anat_func_datagrabber(tmp_path, types=types)
    assert dg.get_element_keys() == ["subject", "session", "task"]
    # sub-03 has no BOLD data
    assert dg.get_elements() == [
        (subject, session, task)
        for subject in ("sub-01", "sub-02")
        for session in ("ses-1", "ses-2")
        for task in ("movie", "rest")
    ]
    out = dg[("sub-02", "ses-1", "rest")]
    assert out["BOLD"]["meta"]["element"] == {
        "subject": "sub-02",
        "session": "ses-1",
        "task": "rest",
    }
    if "VBM_GM" in types:
        assert out["VBM_GM"]["path"].name == "sub-02_GM.nii"


def test_PatternDataGrabber_elements_join(tmp_path: Path) -> None:
    """Test PatternDataGrabber elements of data types with other replacements.

    No pattern has all the replacements, so the elements of each data type are
    joined on the common replacements.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    (tmp_path / "func").mkdir()
    (tmp_path / "dwi").mkdir()
    for task in ("rest", "movie"):
        (tmp_path / "func" / f"sub-01_task-{task}.nii").touch()
    (tmp_path / "func" / "sub-02_task-rest.nii").touch()
    for session in ("ses-1", "ses-2"):
        (tmp_path / "dwi" / f"sub-01_{session}.nii").touch()
    dg = PatternDataGrabber(
        datadir=tmp_path,
        types=["BOLD", "DWI"],
        patterns={
            "BOLD": {
                "pattern": "func/{subject}_task-{task}.nii",
                "space": "MNI152NLin6Asym",
            },
            "DWI": {"pattern": "dwi/{subject}_{session}.nii"},
        },
        replacements=["subject", "session", "task"],
        partial_pattern_ok=True,
    )
    assert dg.get_element_keys() == ["subject", "session", "task"]
    # sub-02 has no DWI data
    assert dg.get_elements() == [
        ("sub-01", session, task)
        for session in ("ses-1", "ses-2")
        for task in ("movie", "rest")
    ]


@pytest.mark.parametrize(
    "types, values, expected",
    [
        (
            ["BOLD"],
            {"task": ["rest"]},
            [
                (subject, session, "rest")
                for subject in ("sub-01", "sub-02")
                for session in ("ses-1", "ses-2")
            ],
        ),
        (
            ["BOLD", "VBM_GM"],
            {"subject": ["sub-02", "sub-03"], "task": ["movie"]},
            [("sub-02", "ses-1", "movie"), ("sub-02", "ses-2", "movie")],
        ),
        # The task is ignored, as the VBM data does not depend on it
        (["VBM_GM"], {"task": ["rest"]}, ["sub-01", "sub-02", "sub-03"]),
        (["VBM_GM"], {"subject": ["sub-02"]}, ["sub-02"]),
    ],
)
def test_PatternDataGrabber_replacement_values(
    tmp_path: Path,
    types: list[str],
    values: dict[str, list[str]],
    expected: list,
) -> None:
    """Test PatternDataGrabber with the values of replacements to grab.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    types : list of str
        The parametrized data types.
    values : dict of str and list of str
        The parametrized values of the replacements to grab.
    expected : list
        The parametrized elements.

    """
    replacements = {k: values.get(k) for k in ("subject", "session", "task")}
    dg = _anat_func_datagrabber(
        tmp_path, types=types, replacements=replacements
    )
    assert dg.get_replacement_values() == values
    assert dg.get_elements() == expected
    for element in expected:
        dg[element]


def test_PatternDataGrabber_replacement_values_get_item(
    tmp_path: Path,
) -> None:
    """Test PatternDataGrabber only grabs the values of the replacements.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    dg = _anat_func_datagrabber(
        tmp_path,
        types=["BOLD"],
        replacements={"subject": None, "session": None, "task": ["rest"]},
    )
    dg[("sub-01", "ses-1", "rest")]
    # The file exists, but the task is not one of the values to grab
    with pytest.raises(ValueError, match="`movie` of `task` is not one"):
        dg[("sub-01", "ses-1", "movie")]


class _Tasks(StrEnum):
    """Tasks of the test datagrabber."""

    REST = "rest"
    MOVIE = "movie"


class _TasksDataGrabber(PatternDataGrabber):
    """Test datagrabber with a field with the tasks to grab."""

    tasks: _Tasks | list[_Tasks] | None = None
    _REPLACEMENT_FIELDS: ClassVar[dict[str, str]] = {"task": "tasks"}


@pytest.mark.parametrize(
    "tasks, expected",
    [
        (None, ["movie", "rest"]),
        ([_Tasks.REST], ["rest"]),
        ("movie", ["movie"]),
    ],
)
def test_PatternDataGrabber_replacement_fields(
    tmp_path: Path, tasks: list | str | None, expected: list[str]
) -> None:
    """Test PatternDataGrabber with a field with the values of a replacement.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    tasks : list or str or None
        The parametrized tasks to grab.
    expected : list of str
        The parametrized tasks of the elements.

    """
    _anat_func_files(tmp_path)
    dg = _TasksDataGrabber(
        datadir=tmp_path,
        types=["BOLD"],
        patterns=deepcopy(_PATTERNS),
        replacements=["subject", "session", "task"],
        tasks=tasks,
    )
    assert sorted({task for _, _, task in dg.get_elements()}) == expected
    if tasks is not None:
        assert dg.get_replacement_values() == {"task": expected}
        with pytest.raises(ValueError, match="is not one of the values"):
            dg[
                (
                    "sub-01",
                    "ses-1",
                    "movie" if expected == ["rest"] else "rest",
                )
            ]


@pytest.mark.parametrize(
    "replacements, match",
    [
        (
            {"subject": None, "session": None, "task": ["rest"]},
            "given by the field `tasks`",
        ),
        (["subject", "session"], "`task` of the field `tasks` is not one"),
    ],
)
def test_PatternDataGrabber_replacement_fields_error(
    tmp_path: Path, replacements: list | dict, match: str
) -> None:
    """Test PatternDataGrabber errors with fields of replacements.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    replacements : list or dict
        The parametrized replacements.
    match : str
        The parametrized error message.

    """
    patterns = deepcopy(_PATTERNS)
    patterns["BOLD"]["pattern"] = patterns["BOLD"]["pattern"].replace(
        "task-{task}", "task-rest"
    )
    with pytest.raises(ValueError, match=match):
        _TasksDataGrabber(
            datadir=tmp_path,
            types=["BOLD"],
            patterns=(
                patterns
                if isinstance(replacements, list)
                else deepcopy(_PATTERNS)
            ),
            replacements=replacements,
            tasks=["rest"],
        )


@pytest.mark.parametrize(
    "files, pattern, expected",
    [
        # Wildcard for any characters
        (
            [
                "sub-01/func/sub-01_task-rest_acq-mb3_bold.nii",
                "sub-01/func/sub-01_task-faces_acq-seq_bold.nii",
                "sub-02/func/sub-02_task-rest_acq-mb3_bold.nii",
            ],
            "{subject}/func/{subject}_task-{task}_acq-*_bold.nii",
            [("sub-01", "faces"), ("sub-01", "rest"), ("sub-02", "rest")],
        ),
        # Wildcard for one character
        (
            [
                "sub-01/rfMRI_rest/rfMRI_rest.nii",
                "sub-01/tfMRI_faces/tfMRI_faces.nii",
            ],
            "{subject}/?fMRI_{task}/?fMRI_{task}.nii",
            [("sub-01", "faces"), ("sub-01", "rest")],
        ),
        # Characters of regular expressions
        (
            ["fmriprep+/sub-01/sub-01_task-rest.nii"],
            "fmriprep+/{subject}/{subject}_task-{task}.nii",
            [("sub-01", "rest")],
        ),
    ],
)
def test_PatternDataGrabber_wildcards(
    tmp_path: Path, files: list[str], pattern: str, expected: list[tuple]
) -> None:
    """Test PatternDataGrabber with unix glob wildcards in the patterns.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    files : list of str
        The parametrized files to create.
    pattern : str
        The parametrized pattern.
    expected : list of tuple
        The parametrized elements.

    """
    for fname in files:
        (tmp_path / fname).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / fname).touch()
    dg = PatternDataGrabber(
        datadir=tmp_path,
        types=["BOLD"],
        patterns={"BOLD": {"pattern": pattern, "space": "native"}},
        replacements=["subject", "task"],
    )
    assert dg.get_elements() == expected
    # Each element is one of the files
    paths = {dg[element]["BOLD"]["path"] for element in expected}
    assert paths == {tmp_path / fname for fname in files}


@pytest.mark.parametrize(
    "pattern",
    [
        "{subject}/{subject}_task-{task}_bold.nii",
        "{subject}/{subject}_task-{task}_*.nii",
    ],
)
def test_PatternDataGrabber_absolute_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pattern: str
) -> None:
    """Test PatternDataGrabber paths are absolute with a relative datadir.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    monkeypatch : pytest.MonkeyPatch
        The pytest.MonkeyPatch object.
    pattern : str
        The parametrized pattern, with and without wildcards.

    """
    (tmp_path / "data" / "sub-01").mkdir(parents=True)
    (tmp_path / "data" / "sub-01" / "sub-01_task-rest_bold.nii").touch()
    monkeypatch.chdir(tmp_path)
    dg = PatternDataGrabber(
        datadir="data",
        types=["BOLD"],
        patterns={"BOLD": {"pattern": pattern, "space": "native"}},
        replacements=["subject", "task"],
    )
    path = dg[("sub-01", "rest")]["BOLD"]["path"]
    assert path.is_absolute()
    assert path == tmp_path / "data" / "sub-01" / "sub-01_task-rest_bold.nii"
