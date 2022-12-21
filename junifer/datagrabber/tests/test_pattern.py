"""Provide tests for pattern."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

import pytest

from junifer.datagrabber.pattern import PatternDataGrabber


def test_PatternDataGrabber_errors(tmp_path: Path) -> None:
    """Test PatternDataGrabber errors.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """

    with pytest.raises(TypeError, match=r"`types` must be a list"):
        PatternDataGrabber(
            datadir="/tmp",
            types="wrong",  # type: ignore
            patterns={"wrong": "pattern"},
            replacements="subject",  # type: ignore
        )

    with pytest.raises(TypeError, match=r"`types` must be a list of strings"):
        PatternDataGrabber(
            datadir="/tmp",  # type: ignore
            types=[1, 2, 3],  # type: ignore
            patterns={"1": "pattern", "2": "pattern", "3": "pattern"},
            replacements="subject",  # type: ignore
        )

    with pytest.raises(ValueError, match=r"must have the same length"):
        PatternDataGrabber(
            datadir="/tmp",
            types=["func", "anat"],
            patterns={"1": "pattern", "2": "pattern", "3": "pattern"},
            replacements=1,  # type: ignore
        )

    with pytest.raises(TypeError, match=r"`patterns` must be a dict"):
        PatternDataGrabber(
            datadir="/tmp",
            types=["func", "anat"],
            patterns="wrong",  # type: ignore
            replacements="subject",  # type: ignore
        )

    with pytest.raises(
        ValueError, match=r"`patterns` must have the same length"
    ):
        PatternDataGrabber(
            datadir="/tmp",
            types=["func", "anat"],
            patterns={"wrong": "pattern"},
            replacements="subject",  # type: ignore
        )

    with pytest.raises(
        ValueError, match=r"`patterns` must contain all `types`"
    ):
        PatternDataGrabber(
            datadir="/tmp",
            types=["func", "anat"],
            patterns={"wrong": "pattern", "func": "pattern"},
            replacements="subject",  # type: ignore
        )

    with pytest.raises(TypeError, match=r"must be a list of strings"):
        PatternDataGrabber(
            datadir="/tmp",
            types=["func", "anat"],
            patterns={"func": "func/test", "anat": "anat/test"},
            replacements=1,  # type: ignore
        )

    with pytest.raises(ValueError, match=r"not part of any pattern"):
        PatternDataGrabber(
            datadir="/tmp",
            types=["func", "anat"],
            patterns={
                "func": "func/{subject}.nii",
                "anat": "anat/{subject}.nii",
            },
            replacements=["subject", "wrong"],
        )

    tmpdir = tmp_path / "pattern_dg_test_errors"

    datagrabber = PatternDataGrabber(
        datadir=tmpdir,
        types=["func", "anat"],
        patterns={
            "func": "func/{subject}_single.nii",
            "anat": "anat/{subject}_{session}_ses.nii",
        },
        replacements=["subject", "session"],
    )

    with pytest.raises(ValueError, match="element keys must be"):
        datagrabber["sub001"]

    # This should not work, file does not exists
    with pytest.raises(ValueError, match="Cannot access"):
        datagrabber["sub001", "ses001"]

    (tmpdir / "func").mkdir(exist_ok=True, parents=True)
    (tmpdir / "anat").mkdir(exist_ok=True, parents=True)
    for t_subject in range(3):
        for t_session in range(2):
            subject = f"sub{t_subject:03d}"
            session = f"ses{t_session:03d}"
            (tmpdir / "func" / f"{subject}_single.nii").touch()
            if t_subject == 2:
                (tmpdir / "func" / f"{subject}_extra.nii").touch()
            (tmpdir / "anat" / f"{subject}_{session}_ses.nii").touch()

    # This should work, file now exists
    datagrabber["sub001", "ses001"]

    datagrabber = PatternDataGrabber(
        datadir=tmpdir,
        types=["func", "anat"],
        patterns={
            "func": "func/{subject}_*.nii",
            "anat": "anat/{subject}_{session}_*.nii",
        },
        replacements=["subject", "session"],
    )

    # access a subject with a missing session
    with pytest.raises(ValueError, match="No file matches"):
        datagrabber["sub001", "ses004"]

    # access a subject with two matching files
    with pytest.raises(ValueError, match="More than one"):
        datagrabber["sub002", "ses001"]

    # access the right one
    datagrabber["sub001", "ses001"]

    datagrabber = PatternDataGrabber(
        datadir=tmpdir,
        types=["func", "anat2"],
        patterns={
            "func": "func/{subject}_single.nii",
            "anat2": "anat2/{subject}_{session}_ses.nii",
        },
        replacements=["subject", "session"],
    )
    assert len(datagrabber.get_elements()) == 0


def test_PatternDataGrabber(tmp_path: Path) -> None:
    """Test PatternDataGrabber.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """

    datagrabber = PatternDataGrabber(
        datadir="/tmp/data",
        types=["func", "anat"],
        patterns={"func": "func/{subject}.nii", "anat": "anat/{subject}.nii"},
        replacements="subject",
    )
    assert datagrabber.datadir == Path("/tmp/data")
    assert datagrabber.types == ["func", "anat"]
    assert datagrabber.replacements == ["subject"]

    datagrabber = PatternDataGrabber(
        datadir=Path("/tmp/data"),
        types=["func", "anat"],
        patterns={
            "func": "func/{subject}.nii",
            "anat": "anat/{subject}_{session}.nii",
        },
        replacements=["subject", "session"],
    )
    assert datagrabber.datadir == Path("/tmp/data")
    assert datagrabber.types == ["func", "anat"]
    assert datagrabber.replacements == ["subject", "session"]

    tmpdir = tmp_path / "pattern_dg_test"
    (tmpdir / "func").mkdir(exist_ok=True, parents=True)
    (tmpdir / "anat").mkdir(exist_ok=True, parents=True)
    (tmpdir / "vbm").mkdir(exist_ok=True, parents=True)
    for t_subject in range(3):
        for t_session in range(2):
            for t_task in range(2, 4):
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

    datagrabber = PatternDataGrabber(
        datadir=tmpdir,
        types=["anat"],
        patterns={
            "anat": "anat/{subject}_{session}.nii",
        },
        replacements=["subject", "session"],
    )

    elements = datagrabber.get_elements()
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

    datagrabber = PatternDataGrabber(
        datadir=tmpdir,
        types=["func", "anat", "vbm"],
        patterns={
            "func": "func/{subject}.nii",
            "anat": "anat/{subject}_{session}.nii",
            "vbm": "vbm/{subject}_{task}_{session}.nii",
        },
        replacements=["subject", "session", "task"],
    )

    elements = datagrabber.get_elements()
    assert set(elements) == set(expected_elements)

    out1 = datagrabber[("sub000", "ses000", "task002")]
    out2 = datagrabber[("sub000", "ses000", "task003")]

    assert out1["func"]["path"] == out2["func"]["path"]
    assert out1["anat"]["path"] == out2["anat"]["path"]
    assert out1["vbm"]["path"] != out2["vbm"]["path"]


def test_pattern_data_grabber_confounds_format_error_on_init() -> None:
    """Test PatterDataGrabber confounds format error on initialisation."""
    with pytest.raises(
        ValueError, match="Invalid value for `confounds_format`"
    ):
        PatternDataGrabber(
            types=["func"],
            patterns={"func": "func/{subject}.nii"},
            replacements=["subject"],
            datadir="/tmp",
            confounds_format="foobar",
        )


def test_pattern_data_grabber_confounds_format_error_on_fetch(
    tmp_path: Path,
) -> None:
    """Test PatterDataGrabber confounds format error on fetching.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    # Create test directory path
    tmpdir = tmp_path / "pattern_dg_test"
    # Create final test directory
    (tmpdir / "func" / "confounds").mkdir(exist_ok=True, parents=True)
    # Create test confound file
    (tmpdir / "func" / "confounds" / "sub-001.nii").touch()
    # Initialise datagrabber
    datagrabber = PatternDataGrabber(
        types=["BOLD_confounds"],
        patterns={"BOLD_confounds": "func/confounds/{subject}.nii"},
        replacements=["subject"],
        datadir=tmpdir,
    )
    # Check error on fetch
    with pytest.raises(
        ValueError, match="As the datagrabber used specifies 'BOLD_confounds'"
    ):
        datagrabber.get_item(subject="sub-001")
