"""Provide tests for PatternDataladDataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

from pydantic import HttpUrl

from junifer.datagrabber import DataType, PatternDataladDataGrabber


_testing_dataset = {
    "example_bids": {
        "uri": "https://gin.g-node.org/juaml/datalad-example-bids",
        "commit": "3f288c8725207ae0c9b3616e093e78cda192b570",
        "id": "8fddff30-6993-420a-9d1e-b5b028c59468",
    },
    "example_bids_ses": {
        "uri": "https://gin.g-node.org/juaml/datalad-example-bids-ses",
        "commit": "6b163aa98af76a9eac0272273c27e14127850181",
        "id": "715c17cf-a1b9-42d6-9af8-9f74c1a4a724",
    },
}


def test_bids_PatternDataladDataGrabber() -> None:
    """Test subject-based BIDS PatternDataladDataGrabber."""
    repo_commit = _testing_dataset["example_bids"]["commit"]
    repo_uri = _testing_dataset["example_bids"]["uri"]
    with PatternDataladDataGrabber(
        uri=HttpUrl(repo_uri),
        types=[DataType.T1w, DataType.BOLD],
        patterns={
            "T1w": {
                "pattern": "{subject}/anat/{subject}_T1w.nii.gz",
                "space": "MNI152NLin6Asym",
            },
            "BOLD": {
                "pattern": "{subject}/func/{subject}_task-rest_bold.nii.gz",
                "space": "MNI152NLin6Asym",
            },
        },
        replacements=["subject"],
        rootdir=Path("example_bids"),
    ) as dg:
        subs = list(dg)
        expected_subs = [f"sub-{i:02d}" for i in range(1, 10)]
        assert set(subs) == set(expected_subs)

        for elem in dg:
            t_sub = dg[elem]
            assert "path" in t_sub["T1w"]
            assert t_sub["T1w"]["path"] == (
                dg.fulldir / f"{elem}/anat/{elem}_T1w.nii.gz"
            )
            assert "path" in t_sub["BOLD"]
            assert t_sub["BOLD"]["path"] == (
                dg.fulldir / f"{elem}/func/{elem}_task-rest_bold.nii.gz"
            )

            assert "meta" in t_sub["BOLD"]
            meta = t_sub["BOLD"]["meta"]
            assert "datagrabber" in meta
            dg_meta = meta["datagrabber"]
            assert "class" in dg_meta
            assert dg_meta["class"] == "PatternDataladDataGrabber"
            assert "uri" in dg_meta
            assert str(dg_meta["uri"]) == repo_uri
            assert "datalad_commit_id" in dg_meta
            assert dg_meta["datalad_commit_id"] == repo_commit

            with open(t_sub["T1w"]["path"]) as f:
                assert f.readlines()[0].startswith("placeholder")


def test_bids_PatternDataladDataGrabber_datadir() -> None:
    """Test PatternDataladDataGrabber with a datadir set to a relative path."""
    datadir = Path("dataset")  # use string and not absolute path
    with PatternDataladDataGrabber(
        uri=HttpUrl(_testing_dataset["example_bids"]["uri"]),
        types=[DataType.T1w, DataType.BOLD],
        patterns={
            "T1w": {
                "pattern": "{subject}/anat/{subject}_T*w.nii.gz",
                "space": "MNI152NLin6Asym",
            },
            "BOLD": {
                "pattern": "{subject}/func/{subject}_task-rest_*.nii.gz",
                "space": "MNI152NLin6Asym",
            },
        },
        replacements=["subject"],
        datadir=datadir,
        rootdir=Path("example_bids"),
    ) as dg:
        assert dg.fulldir == Path(datadir) / "example_bids"
        for elem in dg:
            t_sub = dg[elem]
            assert "path" in t_sub["T1w"]
            assert t_sub["T1w"]["path"] == (
                dg.fulldir / f"{elem}/anat/{elem}_T1w.nii.gz"
            )
            assert "path" in t_sub["BOLD"]
            assert t_sub["BOLD"]["path"] == (
                dg.fulldir / f"{elem}/func/{elem}_task-rest_bold.nii.gz"
            )


def test_bids_PatternDataladDataGrabber_session():
    """Test a subject and session-based BIDS PatternDataladDataGrabber."""
    # Set parameters
    repo_uri = HttpUrl(_testing_dataset["example_bids_ses"]["uri"])
    rootdir = Path("example_bids_ses")
    replacements = ["subject", "session"]
    # With T1W and bold, only 2 sessions are available
    with PatternDataladDataGrabber(
        uri=repo_uri,
        types=[DataType.T1w, DataType.BOLD],
        patterns={
            "T1w": {
                "pattern": (
                    "{subject}/{session}/anat/{subject}_{session}_T1w.nii.gz"
                ),
                "space": "MNI152NLin6Asym",
            },
            "BOLD": {
                "pattern": (
                    "{subject}/{session}/func/"
                    "{subject}_{session}_task-rest_bold.nii.gz"
                ),
                "space": "MNI152NLin6Asym",
            },
        },
        replacements=replacements,
        rootdir=rootdir,
    ) as dg:
        subs = list(dg.get_elements())
        expected_subs = [
            (f"sub-{i:02d}", f"ses-{j:02d}")
            for j in range(1, 3)
            for i in range(1, 10)
        ]
        assert set(subs) == set(expected_subs)

    # Test with a different T1w only, it should have 3 sessions
    with PatternDataladDataGrabber(
        uri=repo_uri,
        types=DataType.T1w,
        patterns={
            "T1w": {
                "pattern": (
                    "{subject}/{session}/anat/{subject}_{session}_T1w.nii.gz"
                ),
                "space": "MNI152NLin6Asym",
            },
        },
        replacements=replacements,
        rootdir=rootdir,
    ) as dg:
        subs = list(dg)
        expected_subs = [
            (f"sub-{i:02d}", f"ses-{j:02d}")
            for j in range(1, 4)
            for i in range(1, 10)
        ]
        assert set(subs) == set(expected_subs)
