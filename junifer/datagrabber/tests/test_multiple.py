"""Provide tests for MultipleDataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

import pytest

from junifer.datagrabber import MultipleDataGrabber, PatternDataladDataGrabber


_testing_dataset = {
    "example_bids": {
        "uri": "https://gin.g-node.org/juaml/datalad-example-bids",
        "id": "522dfb203afcd2cd55799bf347f9b211919a7338",
    },
    "example_bids_ses": {
        "uri": "https://gin.g-node.org/juaml/datalad-example-bids-ses",
        "id": "3d08d55d1faad4f12ab64ac9497544a0d924d47a",
    },
}


def test_MultipleDataGrabber() -> None:
    """Test MultipleDataGrabber."""
    repo_uri = _testing_dataset["example_bids_ses"]["uri"]
    rootdir = "example_bids_ses"
    replacements = ["subject", "session"]

    dg1 = PatternDataladDataGrabber(
        rootdir=rootdir,
        uri=repo_uri,
        types=["T1w"],
        patterns={
            "T1w": {
                "pattern": (
                    "{subject}/{session}/anat/{subject}_{session}_T1w.nii.gz"
                ),
                "space": "native",
            },
        },
        replacements=replacements,
    )

    dg2 = PatternDataladDataGrabber(
        rootdir=rootdir,
        uri=repo_uri,
        types=["BOLD"],
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

    dg = MultipleDataGrabber([dg1, dg2])

    types = dg.get_types()
    assert "T1w" in types
    assert "BOLD" in types

    expected_subs = [
        (f"sub-{i:02d}", f"ses-{j:02d}")
        for j in range(1, 3)
        for i in range(1, 10)
    ]

    with dg:
        subs = list(dg)
        assert set(subs) == set(expected_subs)

        elem = dg[("sub-01", "ses-01")]
        assert "T1w" in elem
        assert "BOLD" in elem
        assert "meta" in elem["BOLD"]
        meta = elem["BOLD"]["meta"]["datagrabber"]
        assert "class" in meta
        assert meta["class"] == "MultipleDataGrabber"
        assert "datagrabbers" in meta
        assert len(meta["datagrabbers"]) == 2
        assert meta["datagrabbers"][0]["class"] == "PatternDataladDataGrabber"
        assert meta["datagrabbers"][1]["class"] == "PatternDataladDataGrabber"


def test_MultipleDataGrabber_no_intersection() -> None:
    """Test MultipleDataGrabber without intersection (0 elements)."""
    rootdir = "example_bids_ses"
    replacements = ["subject", "session"]

    dg1 = PatternDataladDataGrabber(
        rootdir=rootdir,
        uri=_testing_dataset["example_bids"]["uri"],
        types=["T1w"],
        patterns={
            "T1w": {
                "pattern": (
                    "{subject}/{session}/anat/{subject}_{session}_T1w.nii.gz"
                ),
                "space": "native",
            },
        },
        replacements=replacements,
    )

    dg2 = PatternDataladDataGrabber(
        rootdir=rootdir,
        uri=_testing_dataset["example_bids_ses"]["uri"],
        types=["BOLD"],
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

    dg = MultipleDataGrabber([dg1, dg2])
    expected_subs = set()
    with dg:
        subs = list(dg)
        assert set(subs) == set(expected_subs)


def test_MultipleDataGrabber_get_item() -> None:
    """Test MultipleDataGrabber get_item() error."""
    dg1 = PatternDataladDataGrabber(
        rootdir="example_bids_ses",
        uri=_testing_dataset["example_bids"]["uri"],
        types=["T1w"],
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

    dg = MultipleDataGrabber([dg1])
    with pytest.raises(NotImplementedError):
        dg.get_item(subject="sub-01")  # type: ignore


def test_MultipleDataGrabber_validation() -> None:
    """Test MultipleDataGrabber init validation."""
    rootdir = "example_bids_ses"

    dg1 = PatternDataladDataGrabber(
        rootdir=rootdir,
        uri=_testing_dataset["example_bids"]["uri"],
        types=["T1w"],
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
        uri=_testing_dataset["example_bids_ses"]["uri"],
        types=["BOLD"],
        patterns={
            "BOLD": {
                "pattern": "{subject}/func/{subject}_task-rest_bold.nii.gz",
                "space": "MNI152NLin6Asym",
            },
        },
        replacements=["subject"],
    )

    with pytest.raises(RuntimeError, match="have different element keys"):
        MultipleDataGrabber([dg1, dg2])

    with pytest.raises(RuntimeError, match="have overlapping mandatory"):
        MultipleDataGrabber([dg1, dg1])


def test_MultipleDataGrabber_partial_pattern() -> None:
    """Test MultipleDataGrabber partial pattern."""
    dg1 = PatternDataladDataGrabber(
        rootdir=".",
        uri="data://uri1",
        types=["BOLD"],
        patterns={
            "BOLD": {
                "pattern": (
                    "{subject}/{session}/func/"
                    "{subject}_{session}_task-rest_bold.nii.gz"
                ),
                "space": "MNI152NLin6Asym",
            },
        },
        replacements=["subject", "session"],
    )

    dg2 = PatternDataladDataGrabber(
        rootdir=".",
        uri="data://uri2",
        types=["BOLD"],
        patterns={
            "BOLD": {
                "confounds": {
                    "pattern": (
                        "{subject}/{session}/func/"
                        "{subject}_{session}_confounds.tsv"
                    ),
                    "format": "fmriprep",
                },
            },
        },
        replacements=["subject", "session"],
        partial_pattern_ok=True,
    )

    # Test validation works
    MultipleDataGrabber([dg1, dg2])
