"""Provide tests for PatternDataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from itertools import product
from pathlib import Path

import pytest

from junifer.datagrabber import PatternDataGrabber


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
        datadir="/tmp/data",
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
        replacements="subject",
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
        types=["T1w"],
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
        types=["FreeSurfer"],
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


def test_PatternDataGrabber_confounds_format_error_on_init() -> None:
    """Test PatterDataGrabber confounds format error on initialisation."""
    with pytest.raises(
        ValueError, match="Invalid value for `confounds_format`"
    ):
        PatternDataGrabber(
            types=["BOLD"],
            patterns={
                "BOLD": {
                    "pattern": "func/{subject}.nii",
                    "space": "MNI152NLin6Asym",
                },
            },
            replacements=["subject"],
            datadir="/tmp",
            confounds_format="foobar",
        )
