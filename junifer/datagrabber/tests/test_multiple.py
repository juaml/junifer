"""Provide tests for multiple."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from junifer.datagrabber import PatternDataladDataGrabber, MultipleDataGrabber

_testing_dataset = {
    "example_bids": {
        "uri": "https://gin.g-node.org/juaml/datalad-example-bids",
        "id": "e2ce149bd723088769a86c72e57eded009258c6b",
    },
    "example_bids_ses": {
        "uri": "https://gin.g-node.org/juaml/datalad-example-bids-ses",
        "id": "3d08d55d1faad4f12ab64ac9497544a0d924d47a",
    },
}


def test_multiple() -> None:

    repo_uri = _testing_dataset["example_bids_ses"]["uri"]
    rootdir = "example_bids_ses"
    replacements = ["subject", "session"]
    pattern1 = {
        "T1w": "{subject}/{session}/anat/{subject}_{session}_T1w.nii.gz",
    }
    pattern2 = {
        "bold": "{subject}/{session}/func/"
        "{subject}_{session}_task-rest_bold.nii.gz",
    }
    dg1 = PatternDataladDataGrabber(
        rootdir=rootdir,
        uri=repo_uri,
        types=["T1w"],
        patterns=pattern1,
        replacements=replacements)

    dg2 = PatternDataladDataGrabber(
        rootdir=rootdir,
        uri=repo_uri,
        types=["bold"],
        patterns=pattern2,
        replacements=replacements)

    dg = MultipleDataGrabber([dg1, dg2])
    expected_subs = [
        (f"sub-{i:02d}", f"ses-{j:02d}")
        for j in range(1, 3)
        for i in range(1, 10)
    ]

    with dg:
        subs = [x for x in dg]
        assert set(subs) == set(expected_subs)


def test_multiple_no_intersection() -> None:

    repo_uri1 = _testing_dataset["example_bids"]["uri"]
    repo_uri2 = _testing_dataset["example_bids_ses"]["uri"]
    rootdir = "example_bids_ses"
    replacements = ["subject", "session"]
    pattern1 = {
        "T1w": "{subject}/{session}/anat/{subject}_{session}_T1w.nii.gz",
    }
    pattern2 = {
        "bold": "{subject}/{session}/func/"
        "{subject}_{session}_task-rest_bold.nii.gz",
    }
    dg1 = PatternDataladDataGrabber(
        rootdir=rootdir,
        uri=repo_uri1,
        types=["T1w"],
        patterns=pattern1,
        replacements=replacements)

    dg2 = PatternDataladDataGrabber(
        rootdir=rootdir,
        uri=repo_uri2,
        types=["bold"],
        patterns=pattern2,
        replacements=replacements)

    dg = MultipleDataGrabber([dg1, dg2])
    expected_subs = set()
    with dg:
        subs = [x for x in dg]
        assert set(subs) == set(expected_subs)
