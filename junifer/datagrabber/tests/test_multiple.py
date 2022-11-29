"""Provide tests for multiple."""

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


def test_multiple() -> None:
    """Test a multiple datagrabber."""
    repo_uri = _testing_dataset["example_bids_ses"]["uri"]
    rootdir = "example_bids_ses"
    replacements = ["subject", "session"]
    pattern1 = {
        "T1w": "{subject}/{session}/anat/{subject}_{session}_T1w.nii.gz",
    }
    pattern2 = {
        "BOLD": "{subject}/{session}/func/"
        "{subject}_{session}_task-rest_bold.nii.gz",
    }
    dg1 = PatternDataladDataGrabber(
        rootdir=rootdir,
        uri=repo_uri,
        types=["T1w"],
        patterns=pattern1,
        replacements=replacements,
    )

    dg2 = PatternDataladDataGrabber(
        rootdir=rootdir,
        uri=repo_uri,
        types=["BOLD"],
        patterns=pattern2,
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
        subs = [x for x in dg]
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


def test_multiple_no_intersection() -> None:
    """Test a multiple datagrabber without intersection (0 elements)."""
    repo_uri1 = _testing_dataset["example_bids"]["uri"]
    repo_uri2 = _testing_dataset["example_bids_ses"]["uri"]
    rootdir = "example_bids_ses"
    replacements = ["subject", "session"]
    pattern1 = {
        "T1w": "{subject}/{session}/anat/{subject}_{session}_T1w.nii.gz",
    }
    pattern2 = {
        "BOLD": "{subject}/{session}/func/"
        "{subject}_{session}_task-rest_bold.nii.gz",
    }
    dg1 = PatternDataladDataGrabber(
        rootdir=rootdir,
        uri=repo_uri1,
        types=["T1w"],
        patterns=pattern1,
        replacements=replacements,
    )

    dg2 = PatternDataladDataGrabber(
        rootdir=rootdir,
        uri=repo_uri2,
        types=["BOLD"],
        patterns=pattern2,
        replacements=replacements,
    )

    dg = MultipleDataGrabber([dg1, dg2])
    expected_subs = set()
    with dg:
        subs = [x for x in dg]
        assert set(subs) == set(expected_subs)


def test_multiple_get_item() -> None:
    """Test a multiple datagrabber get_item error."""
    repo_uri1 = _testing_dataset["example_bids"]["uri"]
    rootdir = "example_bids_ses"
    replacements = ["subject", "session"]
    pattern1 = {
        "T1w": "{subject}/{session}/anat/{subject}_{session}_T1w.nii.gz",
    }
    dg1 = PatternDataladDataGrabber(
        rootdir=rootdir,
        uri=repo_uri1,
        types=["T1w"],
        patterns=pattern1,
        replacements=replacements,
    )

    dg = MultipleDataGrabber([dg1])
    with pytest.raises(NotImplementedError):
        dg.get_item(subject="sub-01")  # type: ignore


def test_multiple_validation() -> None:
    """Test a multiple datagrabber init validation."""
    repo_uri1 = _testing_dataset["example_bids"]["uri"]
    repo_uri2 = _testing_dataset["example_bids_ses"]["uri"]
    rootdir = "example_bids_ses"
    replacement1 = ["subject", "session"]
    replacement2 = ["subject"]
    pattern1 = {
        "T1w": "{subject}/{session}/anat/{subject}_{session}_T1w.nii.gz",
    }
    pattern2 = {
        "bold": "{subject}/func/{subject}_task-rest_bold.nii.gz",
    }
    dg1 = PatternDataladDataGrabber(
        rootdir=rootdir,
        uri=repo_uri1,
        types=["T1w"],
        patterns=pattern1,
        replacements=replacement1,
    )

    dg2 = PatternDataladDataGrabber(
        rootdir=rootdir,
        uri=repo_uri2,
        types=["bold"],
        patterns=pattern2,
        replacements=replacement2,
    )

    with pytest.raises(ValueError, match="different element key"):
        MultipleDataGrabber([dg1, dg2])

    with pytest.raises(ValueError, match="overlapping types"):
        MultipleDataGrabber([dg1, dg1])
