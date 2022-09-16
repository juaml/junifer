"""Provide tests for pattern."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

import pytest

from junifer.datagrabber.pattern import PatternDataGrabber


def test_PatternDataGrabber_errors(tmp_path: Path) -> None:
    """Test PatternDataGrabber errors."""

    with pytest.raises(TypeError, match=r"`types` must be a list"):
        PatternDataGrabber(
            datadir="/tmp",
            types="wrong",
            patterns={"wrong": "pattern"},
            replacements="subject",
        )

    with pytest.raises(TypeError, match=r"`types` must be a list of strings"):
        PatternDataGrabber(
            datadir="/tmp",
            types=[1, 2, 3],
            patterns={"1": "pattern", "2": "pattern", "3": "pattern"},
            replacements="subject",
        )

    with pytest.raises(ValueError, match=r"must have the same length"):
        PatternDataGrabber(
            datadir="/tmp",
            types=["func", "anat"],
            patterns={"1": "pattern", "2": "pattern", "3": "pattern"},
            replacements=1,
        )

    with pytest.raises(TypeError, match=r"`patterns` must be a dict"):
        PatternDataGrabber(
            datadir="/tmp",
            types=["func", "anat"],
            patterns="wrong",
            replacements="subject",
        )

    with pytest.raises(
        ValueError, match=r"`patterns` must have the same length"
    ):
        PatternDataGrabber(
            datadir="/tmp",
            types=["func", "anat"],
            patterns={"wrong": "pattern"},
            replacements="subject",
        )

    with pytest.raises(
        ValueError, match=r"`patterns` must contain all `types`"
    ):
        PatternDataGrabber(
            datadir="/tmp",
            types=["func", "anat"],
            patterns={"wrong": "pattern", "func": "pattern"},
            replacements="subject",
        )

    with pytest.raises(TypeError, match=r"must be a list of strings"):
        PatternDataGrabber(
            datadir="/tmp",
            types=["func", "anat"],
            patterns={"func": "func/test", "anat": "anat/test"},
            replacements=1,
        )

    with pytest.warns(RuntimeWarning, match=r"not part of any pattern"):
        PatternDataGrabber(
            datadir="/tmp",
            types=["func", "anat"],
            patterns={
                "func": "func/{subject}.nii",
                "anat": "anat/{subject}.nii",
            },
            replacements=["subject", "wrong"],
        )

    tmpdir = tmp_path / 'pattern_dg_test'

    datagrabber = PatternDataGrabber(
        datadir=tmpdir,
        types=["func", "anat"],
        patterns={
            "func": "func/{subject}.nii",
            "anat": "anat/{subject}_{session}.nii",
        },
        replacements=["subject", "session"],
    )

    with pytest.raises(ValueError, match="element length must be"):
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
            (tmpdir / "func" / f"{subject}.nii").touch()
            if t_subject == 2:
                (tmpdir / "func" / f"{subject}_extra.nii").touch()
            (tmpdir / "anat" / f"{subject}_{session}.nii").touch()

    # This should work, file now exists
    datagrabber["sub001", "ses001"]

    datagrabber = PatternDataGrabber(
        datadir=tmpdir,
        types=["func", "anat"],
        patterns={
            "func": "func/{subject}*.nii",
            "anat": "anat/{subject}_{session}*.nii",
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


def test_PatternDataGrabber() -> None:
    """Test PatternDataGrabber."""

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
