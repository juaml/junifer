"""Provide conftest for pytest."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

import pytest

from junifer.datagrabber import PatternDataladDataGrabber
from junifer.utils.singleton import Singleton


@pytest.fixture(autouse=True)
def reset_singletons() -> None:
    """Reset all singletons."""
    to_clean = ["WorkDirManager"]
    to_remove = [
        v for k, v in Singleton.instances.items() if k.__name__ in to_clean
    ]
    Singleton.instances = {
        k: v
        for k, v in Singleton.instances.items()
        if k.__name__ not in to_clean
    }
    # Force deleting the singletons
    for elem in to_remove:
        del elem


@pytest.fixture
def maps_datagrabber(tmp_path: Path) -> PatternDataladDataGrabber:
    """Return a PatternDataladDataGrabber for maps testing.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    dg = PatternDataladDataGrabber(
        uri="https://github.com/OpenNeuroDatasets/ds005226.git",
        types=["BOLD"],
        patterns={
            "BOLD": {
                "pattern": (
                    "derivatives/pre-processed_data/space-MNI/{subject}/"
                    "{subject-padded}_task-{task}_run-{run}_space-MNI152NLin6Asym"
                    "_res-2_desc-preproc_bold.nii.gz"
                ),
                "space": "MNI152NLin6Asym",
            },
        },
        replacements=["subject", "subject-padded", "task", "run"],
    )
    return dg
