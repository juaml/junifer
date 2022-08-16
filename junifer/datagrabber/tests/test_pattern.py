"""Provide tests for pattern."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from junifer.datagrabber.pattern import PatternDataGrabber

from pathlib import Path

import pytest


def test_PatternDataGrabber() -> None:
    """Test PatternDataGrabber."""
    # Create concrete class
    class MyDataGrabber(PatternDataGrabber):
        def get_elements(self):
            return super().get_elements()

    with pytest.raises(TypeError, match=r"`types` must be a list"):
        MyDataGrabber(
            datadir="/tmp",
            types="wrong",
            patterns={"wrong": "pattern"},
            replacements="subject",
        )

    with pytest.raises(TypeError, match=r"`types` must be a list of strings"):
        MyDataGrabber(
            datadir="/tmp",
            types=[1, 2, 3],
            patterns={"1": "pattern", "2": "pattern", "3": "pattern"},
            replacements="subject",
        )

    with pytest.raises(ValueError, match=r"must have the same length"):
        MyDataGrabber(
            datadir="/tmp",
            types=["func", "anat"],
            patterns={"1": "pattern", "2": "pattern", "3": "pattern"},
            replacements=1,
        )

    with pytest.raises(TypeError, match=r"`patterns` must be a dict"):
        MyDataGrabber(
            datadir="/tmp",
            types=["func", "anat"],
            patterns="wrong",
            replacements="subject",
        )

    with pytest.raises(
        ValueError, match=r"`patterns` must have the same length"
    ):
        MyDataGrabber(
            datadir="/tmp",
            types=["func", "anat"],
            patterns={"wrong": "pattern"},
            replacements="subject",
        )

    with pytest.raises(
            ValueError, match=r"`patterns` must contain all `types`"
    ):
        MyDataGrabber(
            datadir="/tmp",
            types=["func", "anat"],
            patterns={"wrong": "pattern", "func": "pattern"},
            replacements="subject",
        )

    with pytest.raises(TypeError, match=r"must be a list of strings"):
        MyDataGrabber(
            datadir="/tmp",
            types=["func", "anat"],
            patterns={"func": "func/test", "anat": "anat/test"},
            replacements=1,
        )

    with pytest.warns(RuntimeWarning, match=r"not part of any pattern"):
        MyDataGrabber(
            datadir="/tmp",
            types=["func", "anat"],
            patterns={
                "func": "func/{subject}.nii",
                "anat": "anat/{subject}.nii",
            },
            replacements=["subject", "wrong"],
        )

    datagrabber = MyDataGrabber(
        datadir="/tmp/data",
        types=["func", "anat"],
        patterns={"func": "func/{subject}.nii", "anat": "anat/{subject}.nii"},
        replacements="subject",
    )
    assert datagrabber.datadir == Path("/tmp/data")
    assert datagrabber.types == ["func", "anat"]
    assert datagrabber.replacements == ["subject"]

    datagrabber = MyDataGrabber(
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
