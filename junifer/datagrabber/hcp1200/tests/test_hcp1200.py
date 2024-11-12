"""Provide tests for HCP1200."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import shutil
import tempfile
from collections.abc import Iterable
from pathlib import Path
from typing import Optional

import pytest

from junifer.datagrabber import HCP1200, DataladHCP1200
from junifer.utils import configure_logging


URI = "https://gin.g-node.org/juaml/datalad-example-hcp1200"


@pytest.fixture(scope="module")
def hcpdg() -> Iterable[DataladHCP1200]:
    """Return a HCP1200 DataGrabber."""
    tmpdir = Path(tempfile.gettempdir())
    dg = DataladHCP1200(datadir=tmpdir / "datadir")
    # Set URI to Gin
    dg.uri = URI
    # Set correct root directory
    dg._rootdir = "."
    with dg:
        for t_elem in dg.get_elements():
            dg[t_elem]
        yield dg
    shutil.rmtree(tmpdir / "datadir", ignore_errors=True)


@pytest.mark.parametrize(
    "tasks, phase_encodings, ica_fix, expected_path_name",
    [
        (None, None, False, "rfMRI_REST1_LR.nii.gz"),
        ("REST1", "LR", False, "rfMRI_REST1_LR.nii.gz"),
        ("REST1", "RL", False, "rfMRI_REST1_RL.nii.gz"),
        ("REST2", "LR", False, "rfMRI_REST2_LR.nii.gz"),
        ("REST2", "RL", False, "rfMRI_REST2_RL.nii.gz"),
        ("SOCIAL", "LR", False, "tfMRI_SOCIAL_LR.nii.gz"),
        ("SOCIAL", "RL", False, "tfMRI_SOCIAL_RL.nii.gz"),
        ("WM", "LR", False, "tfMRI_WM_LR.nii.gz"),
        ("WM", "RL", False, "tfMRI_WM_RL.nii.gz"),
        ("RELATIONAL", "LR", False, "tfMRI_RELATIONAL_LR.nii.gz"),
        ("RELATIONAL", "RL", False, "tfMRI_RELATIONAL_RL.nii.gz"),
        ("EMOTION", "LR", False, "tfMRI_EMOTION_LR.nii.gz"),
        ("EMOTION", "RL", False, "tfMRI_EMOTION_RL.nii.gz"),
        ("LANGUAGE", "LR", False, "tfMRI_LANGUAGE_LR.nii.gz"),
        ("LANGUAGE", "RL", False, "tfMRI_LANGUAGE_RL.nii.gz"),
        ("GAMBLING", "LR", False, "tfMRI_GAMBLING_LR.nii.gz"),
        ("GAMBLING", "RL", False, "tfMRI_GAMBLING_RL.nii.gz"),
        ("MOTOR", "LR", False, "tfMRI_MOTOR_LR.nii.gz"),
        ("MOTOR", "RL", False, "tfMRI_MOTOR_RL.nii.gz"),
        ("REST1", "LR", True, "rfMRI_REST1_LR_hp2000_clean.nii.gz"),
        ("REST1", "RL", True, "rfMRI_REST1_RL_hp2000_clean.nii.gz"),
        ("REST2", "LR", True, "rfMRI_REST2_LR_hp2000_clean.nii.gz"),
        ("REST2", "RL", True, "rfMRI_REST2_RL_hp2000_clean.nii.gz"),
    ],
)
def test_HCP1200(
    hcpdg: DataladHCP1200,
    tasks: Optional[str],
    phase_encodings: Optional[str],
    ica_fix: bool,
    expected_path_name: str,
) -> None:
    """Test HCP1200 DataGrabber.

    Parameters
    ----------
    hcpdg : DataladHCP1200
        The Datalad version of the DataGrabber with the first subject
        already cloned.
    tasks : str
        The parametrized tasks.
    phase_encodings : str
        The parametrized phase encodings.
    ica_fix : bool
        The parametrized ICA-FIX flag.
    expected_path_name : str
        The parametrized expected path name.

    """
    configure_logging(level="DEBUG")
    dg = HCP1200(
        datadir=hcpdg.datadir,
        tasks=tasks,
        phase_encodings=phase_encodings,
        ica_fix=ica_fix,
    )
    # Get all elements
    all_elements = dg.get_elements()
    # Get test element
    test_element = all_elements[0]
    # Get test element data
    out = dg[test_element]
    # Asserts data type
    assert "BOLD" in out
    # Assert data file name
    assert out["BOLD"]["path"].name == expected_path_name
    # Assert data file path exists
    assert out["BOLD"]["path"].exists()
    # Assert data file path is a file
    assert out["BOLD"]["path"].is_file()
    # Assert metadata
    assert "meta" in out["BOLD"]
    meta = out["BOLD"]["meta"]
    assert "element" in meta
    assert "subject" in meta["element"]
    assert test_element[0] == meta["element"]["subject"]


@pytest.mark.parametrize(
    "tasks, phase_encodings",
    [
        ("REST1", "LR"),
        ("REST1", "RL"),
        ("REST2", "LR"),
        ("REST2", "RL"),
        ("SOCIAL", "LR"),
        ("SOCIAL", "RL"),
        ("WM", "LR"),
        ("WM", "RL"),
        ("RELATIONAL", "LR"),
        ("RELATIONAL", "RL"),
        ("EMOTION", "LR"),
        ("EMOTION", "RL"),
        ("LANGUAGE", "LR"),
        ("LANGUAGE", "RL"),
        ("GAMBLING", "LR"),
        ("GAMBLING", "RL"),
        ("MOTOR", "LR"),
        ("MOTOR", "RL"),
    ],
)
def test_HCP1200_single_access(
    hcpdg: DataladHCP1200,
    tasks: Optional[str],
    phase_encodings: Optional[str],
) -> None:
    """Test HCP1200 DataGrabber single access.

    Parameters
    ----------
    hcpdg : DataladHCP1200
        The Datalad version of the DataGrabber with the first subject
        already cloned.
    tasks : str
        The parametrized tasks.
    phase_encodings : str
        The parametrized phase encodings.

    """
    configure_logging(level="DEBUG")
    dg = HCP1200(
        datadir=hcpdg.datadir,
        tasks=tasks,
        phase_encodings=phase_encodings,
    )
    with dg:
        # Get all elements
        all_elements = dg.get_elements()
        # Check only specified task and phase encoding are found
        for element in all_elements:
            assert element[1] == tasks
            assert element[2] == phase_encodings


@pytest.mark.parametrize(
    "tasks, phase_encodings",
    [
        (["REST1", "REST2"], ["LR", "RL"]),
        (["REST1", "REST2"], None),
    ],
)
def test_HCP1200_multi_access(
    hcpdg: DataladHCP1200,
    tasks: Optional[str],
    phase_encodings: Optional[str],
) -> None:
    """Test HCP1200 DataGrabber multiple access.

    Parameters
    ----------
    hcpdg : DataladHCP1200
        The Datalad version of the DataGrabber with the first subject
        already cloned.
    tasks : str
        The parametrized tasks.
    phase_encodings : str
        The parametrized phase encodings.

    """
    configure_logging(level="DEBUG")
    dg = HCP1200(
        datadir=hcpdg.datadir,
        tasks=tasks,
        phase_encodings=phase_encodings,
    )
    with dg:
        # Get all elements
        all_elements = dg.get_elements()
        # Check only specified task and phase encoding are found
        for element in all_elements:
            assert element[1] in ["REST1", "REST2"]
            assert element[2] in ["LR", "RL"]


def test_HCP1200_multi_access_task_simple(
    hcpdg: DataladHCP1200,
) -> None:
    """Test HCP1200 DataGrabber simple multiple access for task.

    Parameters
    ----------
    hcpdg : DataladHCP1200
        The Datalad version of the DataGrabber with the first subject
        already cloned.

    """
    configure_logging(level="DEBUG")
    dg = HCP1200(
        datadir=hcpdg.datadir,
        tasks="REST1",
        phase_encodings=["LR", "RL"],
    )
    with dg:
        # Get all elements
        all_elements = dg.get_elements()
        # Check only specified task and phase encoding are found
        for element in all_elements:
            assert element[1] == "REST1"
            assert element[2] in ["LR", "RL"]


def test_HCP1200_multi_access_phase_simple(
    hcpdg: DataladHCP1200,
) -> None:
    """Test HCP1200 DataGrabber simple multiple access for phase.

    Parameters
    ----------
    hcpdg : DataladHCP1200
        The Datalad version of the DataGrabber with the first subject
        already cloned.

    """
    configure_logging(level="DEBUG")
    dg = HCP1200(
        datadir=hcpdg.datadir,
        tasks=["REST1", "REST2"],
        phase_encodings="LR",
    )
    with dg:
        # Get all elements
        all_elements = dg.get_elements()
        # Check only specified task and phase encoding are found
        for element in all_elements:
            assert element[1] in ["REST1", "REST2"]
            assert element[2] == "LR"


@pytest.mark.parametrize(
    "tasks, phase_encodings",
    [
        ("FOO", ["LR", "RL"]),
        ("FOO", "RL"),
        (["FOO", "BAR"], ["LR", "RL"]),
        (["FOO", "BAR"], "LR"),
    ],
)
def test_HCP1200_incorrect_access_task(
    tasks: Optional[str],
    phase_encodings: Optional[str],
) -> None:
    """Test HCP1200 DataGrabber incorrect access for task.

    Parameters
    ----------
    tasks : str
        The parametrized tasks.
    phase_encodings : str
        The parametrized phase encodings.

    """
    configure_logging(level="DEBUG")
    with pytest.raises(ValueError, match="not a valid HCP-YA fMRI task input"):
        _ = HCP1200(
            datadir=".",
            tasks=tasks,
            phase_encodings=phase_encodings,
        )


@pytest.mark.parametrize(
    "tasks, phase_encodings",
    [
        ("REST1", ["FOO", "BAR"]),
        ("REST1", "FOO"),
        (["REST1", "REST2"], ["FOO", "BAR"]),
        (["REST1", "REST2"], "BAR"),
    ],
)
def test_HCP1200_incorrect_access_phase(
    tasks: Optional[str],
    phase_encodings: Optional[str],
) -> None:
    """Test HCP1200 DataGrabber incorrect access for phase.

    Parameters
    ----------
    tasks : str
        The parametrized tasks.
    phase_encodings : str
        The parametrized phase encodings.

    """
    configure_logging(level="DEBUG")
    with pytest.raises(ValueError, match="not a valid HCP-YA phase encoding"):
        _ = HCP1200(
            datadir=".",
            tasks=tasks,
            phase_encodings=phase_encodings,
        )


def test_HCP1200_elements(
    hcpdg: DataladHCP1200,
) -> None:
    """Test HCP1200 DataGrabber elements.

    Parameters
    ----------
    hcpdg : DataladHCP1200
        The Datalad version of the DataGrabber with the first subject
        already cloned.

    """
    configure_logging(level="DEBUG")
    dg = HCP1200(
        datadir=hcpdg.datadir,
        tasks="REST1",
        phase_encodings="LR",
    )
    with dg:
        # Get all elements
        expected_subjects = [f"sub-{x:02d}" for x in range(1, 10)]
        found_subjects = []
        all_elements = dg.get_elements()
        # Check only specified task and phase encoding are found
        for element in all_elements:
            found_subjects.append(element[0])
            assert element[1] == "REST1"
            assert element[2] in ["LR", "RL"]

        assert set(found_subjects) == set(expected_subjects)


@pytest.mark.parametrize(
    "tasks, ica_fix",
    [
        ("SOCIAL", True),
        ("WM", True),
        ("RELATIONAL", True),
        ("EMOTION", True),
        ("LANGUAGE", True),
        ("GAMBLING", True),
        ("MOTOR", True),
    ],
)
def test_HCP1200_incorrect_access_icafix(
    tasks: Optional[str], ica_fix: bool
) -> None:
    """Test HCP1200 DataGrabber incorrect access for icafix.

    Parameters
    ----------
    tasks : str
        The parametrized tasks.
    ica_fix : bool
        The parametrized ICA-FIX flag.

    """
    configure_logging(level="DEBUG")
    with pytest.raises(ValueError, match="is only available for"):
        _ = HCP1200(
            datadir=".",
            tasks=tasks,
            ica_fix=ica_fix,
        )
