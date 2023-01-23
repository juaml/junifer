"""Provide tests for HCP1200."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Optional, Iterable

import pytest

from junifer.datagrabber.hcp import DataladHCP1200, HCP1200
from junifer.utils import configure_logging


URI = "https://gin.g-node.org/juaml/datalad-example-hcp1200"


@pytest.fixture(scope="module")
def hcpdg() -> Iterable[DataladHCP1200]:
    """Return a HCP1200 datagrabber."""
    dg = DataladHCP1200()
    # Set URI to Gin
    dg.uri = URI
    # Set correct root directory
    dg._rootdir = "."
    with dg:
        for t_elem in dg.get_elements():
            dg[t_elem]
        yield dg


@pytest.mark.parametrize(
    "tasks, phase_encodings, expected_path_name",
    [
        (None, None, "rfMRI_REST1_LR_hp2000_clean.nii.gz"),
        ("REST1", "LR", "rfMRI_REST1_LR_hp2000_clean.nii.gz"),
        ("REST1", "RL", "rfMRI_REST1_RL_hp2000_clean.nii.gz"),
        ("REST2", "LR", "rfMRI_REST2_LR_hp2000_clean.nii.gz"),
        ("REST2", "RL", "rfMRI_REST2_RL_hp2000_clean.nii.gz"),
        ("SOCIAL", "LR", "tfMRI_SOCIAL_LR_hp2000_clean.nii.gz"),
        ("SOCIAL", "RL", "tfMRI_SOCIAL_RL_hp2000_clean.nii.gz"),
        ("WM", "LR", "tfMRI_WM_LR_hp2000_clean.nii.gz"),
        ("WM", "RL", "tfMRI_WM_RL_hp2000_clean.nii.gz"),
        ("RELATIONAL", "LR", "tfMRI_RELATIONAL_LR_hp2000_clean.nii.gz"),
        ("RELATIONAL", "RL", "tfMRI_RELATIONAL_RL_hp2000_clean.nii.gz"),
        ("EMOTION", "LR", "tfMRI_EMOTION_LR_hp2000_clean.nii.gz"),
        ("EMOTION", "RL", "tfMRI_EMOTION_RL_hp2000_clean.nii.gz"),
        ("LANGUAGE", "LR", "tfMRI_LANGUAGE_LR_hp2000_clean.nii.gz"),
        ("LANGUAGE", "RL", "tfMRI_LANGUAGE_RL_hp2000_clean.nii.gz"),
        ("GAMBLING", "LR", "tfMRI_GAMBLING_LR_hp2000_clean.nii.gz"),
        ("GAMBLING", "RL", "tfMRI_GAMBLING_RL_hp2000_clean.nii.gz"),
        ("MOTOR", "LR", "tfMRI_MOTOR_LR_hp2000_clean.nii.gz"),
        ("MOTOR", "RL", "tfMRI_MOTOR_RL_hp2000_clean.nii.gz"),
    ],
)
def test_hcp1200_datagrabber(
    hcpdg: DataladHCP1200,
    tasks: Optional[str],
    phase_encodings: Optional[str],
    expected_path_name: str,
) -> None:
    """Test HCP1200 datagrabber.

    Parameters
    ----------
    hcpdg : DataladHCP1200
        The Datalad version of the datagrabber with the first subject
        already cloned.
    tasks : str
        The parametrized tasks.
    phase_encodings : str
        The parametrized phase encodings.
    expected_path_name : str
        The parametrized expected path name.

    """
    configure_logging(level="DEBUG")
    dg = HCP1200(
        datadir=hcpdg.datadir,
        tasks=tasks,
        phase_encodings=phase_encodings,
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
def test_hcp1200_datagrabber_single_access(
    hcpdg: DataladHCP1200,
    tasks: Optional[str],
    phase_encodings: Optional[str],
) -> None:
    """Test HCP1200 datagrabber single access.

    Parameters
    ----------
    hcpdg : DataladHCP1200
        The Datalad version of the datagrabber with the first subject
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
def test_hcp1200_datagrabber_multi_access(
    hcpdg: DataladHCP1200,
    tasks: Optional[str],
    phase_encodings: Optional[str],
) -> None:
    """Test HCP1200 datagrabber multiple access.

    Parameters
    ----------
    hcpdg : DataladHCP1200
        The Datalad version of the datagrabber with the first subject
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


def test_hcp1200_datagrabber_multi_access_task_simple(
    hcpdg: DataladHCP1200,
) -> None:
    """Test HCP1200 datagrabber simple multiple access for task.

    Parameters
    ----------
    hcpdg : DataladHCP1200
        The Datalad version of the datagrabber with the first subject
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


def test_hcp1200_datagrabber_multi_access_phase_simple(
    hcpdg: DataladHCP1200,
) -> None:
    """Test HCP1200 datagrabber simple multiple access for phase.

    Parameters
    ----------
    hcpdg : DataladHCP1200
        The Datalad version of the datagrabber with the first subject
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
def test_hcp1200_datagrabber_incorrect_access_task(
    tasks: Optional[str],
    phase_encodings: Optional[str],
) -> None:
    """Test HCP1200 datagrabber incorrect access for task.

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
def test_hcp1200_datagrabber_incorrect_access_phase(
    tasks: Optional[str],
    phase_encodings: Optional[str],
) -> None:
    """Test HCP1200 datagrabber incorrect access for phase.

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


def test_hcp1200_datagrabber_elements(
    hcpdg: DataladHCP1200,
) -> None:
    """Test HCP1200 datagrabber elements.

    Parameters
    ----------
    hcpdg : DataladHCP1200
        The Datalad version of the datagrabber with the first subject
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
        expected_subjects = [
            f"sub-{x:02d}" for x in range(1, 10)
        ]
        found_subjects = []
        all_elements = dg.get_elements()
        # Check only specified task and phase encoding are found
        for element in all_elements:
            found_subjects.append(element[0])
            assert element[1] == "REST1"
            assert element[2] in ["LR", "RL"]

        assert set(found_subjects) == set(expected_subjects)
