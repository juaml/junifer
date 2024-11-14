"""Provide tests for DMCC13Benchmark DataGrabber."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Optional, Union

import pytest

from junifer.datagrabber import DMCC13Benchmark


URI = "https://gin.g-node.org/synchon/datalad-example-dmcc13-benchmark"


@pytest.mark.parametrize(
    "sessions, tasks, phase_encodings, runs, native_t1w",
    [
        (None, None, None, None, False),
        ("ses-wave1bas", "Rest", "AP", "1", False),
        ("ses-wave1bas", "Axcpt", "AP", "1", False),
        ("ses-wave1bas", "Cuedts", "AP", "1", False),
        ("ses-wave1bas", "Stern", "AP", "1", False),
        ("ses-wave1bas", "Stroop", "AP", "1", False),
        ("ses-wave1bas", "Rest", "PA", "2", False),
        ("ses-wave1bas", "Axcpt", "PA", "2", False),
        ("ses-wave1bas", "Cuedts", "PA", "2", False),
        ("ses-wave1bas", "Stern", "PA", "2", False),
        ("ses-wave1bas", "Stroop", "PA", "2", False),
        ("ses-wave1bas", "Rest", "AP", "1", True),
        ("ses-wave1bas", "Axcpt", "AP", "1", True),
        ("ses-wave1bas", "Cuedts", "AP", "1", True),
        ("ses-wave1bas", "Stern", "AP", "1", True),
        ("ses-wave1bas", "Stroop", "AP", "1", True),
        ("ses-wave1bas", "Rest", "PA", "2", True),
        ("ses-wave1bas", "Axcpt", "PA", "2", True),
        ("ses-wave1bas", "Cuedts", "PA", "2", True),
        ("ses-wave1bas", "Stern", "PA", "2", True),
        ("ses-wave1bas", "Stroop", "PA", "2", True),
        ("ses-wave1pro", "Rest", "AP", "1", False),
        ("ses-wave1pro", "Rest", "PA", "2", False),
        ("ses-wave1pro", "Rest", "AP", "1", True),
        ("ses-wave1pro", "Rest", "PA", "2", True),
        ("ses-wave1rea", "Rest", "AP", "1", False),
        ("ses-wave1rea", "Rest", "PA", "2", False),
        ("ses-wave1rea", "Rest", "AP", "1", True),
        ("ses-wave1rea", "Rest", "PA", "2", True),
    ],
)
def test_DMCC13Benchmark(
    sessions: Optional[str],
    tasks: Optional[str],
    phase_encodings: Optional[str],
    runs: Optional[str],
    native_t1w: bool,
) -> None:
    """Test DMCC13Benchmark DataGrabber.

    Parameters
    ----------
    sessions : str or None
        The parametrized session values.
    tasks : str or None
        The parametrized task values.
    phase_encodings : str or None
        The parametrized phase encoding values.
    runs : str or None
        The parametrized run values.
    native_t1w : bool
        The parametrized values for fetching native T1w.

    """
    dg = DMCC13Benchmark(
        sessions=sessions,
        tasks=tasks,
        phase_encodings=phase_encodings,
        runs=runs,
        native_t1w=native_t1w,
    )
    # Set URI to Gin
    dg.uri = URI

    with dg:
        # Get all elements
        all_elements = dg.get_elements()
        # Get test element
        test_element = all_elements[0]
        # Get test element's access values
        _, ses, task, phase, run = test_element
        # Access data
        out = dg[("sub-01", ses, task, phase, run)]

        # Available data types
        data_types = [
            "BOLD",
            "VBM_CSF",
            "VBM_GM",
            "VBM_WM",
            "T1w",
        ]
        # Add Warp if native T1w is accessed
        if native_t1w:
            data_types.append("Warp")

        # Data type file name formats
        data_file_names = [
            (
                f"sub-01_{ses}_task-{task}_acq-mb4{phase}_run-{run}_"
                "space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz"
            ),
            "sub-01_space-MNI152NLin2009cAsym_label-CSF_probseg.nii.gz",
            "sub-01_space-MNI152NLin2009cAsym_label-GM_probseg.nii.gz",
            "sub-01_space-MNI152NLin2009cAsym_label-WM_probseg.nii.gz",
        ]
        if native_t1w:
            data_file_names.extend(
                [
                    "sub-01_desc-preproc_T1w.nii.gz",
                    [
                        "sub-01_from-MNI152NLin2009cAsym_to-T1w"
                        "_mode-image_xfm.h5",
                        "sub-01_from-T1w_to-MNI152NLin2009cAsym"
                        "_mode-image_xfm.h5",
                    ],
                ]
            )
        else:
            data_file_names.append(
                "sub-01_space-MNI152NLin2009cAsym_desc-preproc_T1w.nii.gz"
            )

        for data_type, data_file_name in zip(data_types, data_file_names):
            # Assert data type
            assert data_type in out
            # Conditional for Warp
            if data_type == "Warp":
                for idx, fname in enumerate(data_file_name):
                    # Assert data file path exists
                    assert out[data_type][idx]["path"].exists()
                    # Assert data file path is a file
                    assert out[data_type][idx]["path"].is_file()
                    # Assert data file name
                    assert out[data_type][idx]["path"].name == fname
                    # Assert metadata
                    assert "meta" in out[data_type][idx]
            else:
                # Assert data file path exists
                assert out[data_type]["path"].exists()
                # Assert data file path is a file
                assert out[data_type]["path"].is_file()
                # Assert data file name
                assert out[data_type]["path"].name == data_file_name
                # Assert metadata
                assert "meta" in out[data_type]

        # Check BOLD nested data types
        for type_, file_name in zip(
            ("mask", "confounds"),
            (
                (
                    f"sub-01_{ses}_task-{task}_acq-mb4{phase}_run-{run}_"
                    "space-MNI152NLin2009cAsym_desc-brain_mask.nii.gz"
                ),
                (
                    f"sub-01_{ses}_task-{task}_acq-mb4{phase}_run-{run}_"
                    "desc-confounds_regressors.tsv"
                ),
            ),
        ):
            # Assert data type
            assert type_ in out["BOLD"]
            # Assert data file path exists
            assert out["BOLD"][type_]["path"].exists()
            # Assert data file path is a file
            assert out["BOLD"][type_]["path"].is_file()
            # Assert data file name
            assert out["BOLD"][type_]["path"].name == file_name

        # Check T1w nested data types
        # Assert data type
        assert "mask" in out["T1w"]
        # Assert data file path exists
        assert out["T1w"]["mask"]["path"].exists()
        # Assert data file path is a file
        assert out["T1w"]["mask"]["path"].is_file()
        # Assert data file name
        if native_t1w:
            assert (
                out["T1w"]["mask"]["path"].name
                == "sub-01_desc-brain_mask.nii.gz"
            )
        else:
            assert (
                out["T1w"]["mask"]["path"].name
                == "sub-01_space-MNI152NLin2009cAsym_desc-brain_mask.nii.gz"
            )


@pytest.mark.parametrize(
    "types, native_t1w",
    [
        ("BOLD", True),
        ("BOLD", False),
        ("T1w", True),
        ("T1w", False),
        ("VBM_CSF", True),
        ("VBM_CSF", False),
        ("VBM_GM", True),
        ("VBM_GM", False),
        ("VBM_WM", True),
        ("VBM_WM", False),
        (["BOLD", "VBM_CSF"], True),
        (["BOLD", "VBM_CSF"], False),
        (["T1w", "VBM_CSF"], True),
        (["T1w", "VBM_CSF"], False),
        (["VBM_GM", "VBM_WM"], True),
        (["VBM_GM", "VBM_WM"], False),
    ],
)
def test_DMCC13Benchmark_partial_data_access(
    types: Union[str, list[str]],
    native_t1w: bool,
) -> None:
    """Test DMCC13Benchmark DataGrabber partial data access.

    Parameters
    ----------
    types : str or list of str
        The parametrized types.
    native_t1w : bool
        The parametrized values for fetching native T1w.

    """
    dg = DMCC13Benchmark(types=types, native_t1w=native_t1w)
    # Set URI to Gin
    dg.uri = URI

    with dg:
        # Get all elements
        all_elements = dg.get_elements()
        # Get test element
        test_element = all_elements[0]
        # Get test element's access values
        _, ses, task, phase, run = test_element
        # Access data
        out = dg[("sub-01", ses, task, phase, run)]
        # Assert data type
        if isinstance(types, list):
            for type_ in types:
                assert type_ in out
        else:
            assert types in out


def test_DMCC13Benchmark_incorrect_data_type() -> None:
    """Test DMCC13Benchmark DataGrabber incorrect data type."""
    with pytest.raises(
        ValueError, match="`patterns` must contain all `types`"
    ):
        _ = DMCC13Benchmark(types="Orcus")


def test_DMCC13Benchmark_invalid_sessions():
    """Test DMCC13Benchmark DataGrabber invalid sessions."""
    with pytest.raises(
        ValueError,
        match=("phonyses is not a valid session in " "the DMCC dataset"),
    ):
        DMCC13Benchmark(sessions="phonyses")


def test_DMCC13Benchmark_invalid_tasks():
    """Test DMCC13Benchmark DataGrabber invalid tasks."""
    with pytest.raises(
        ValueError,
        match=(
            "thisisnotarealtask is not a valid task in " "the DMCC dataset"
        ),
    ):
        DMCC13Benchmark(tasks="thisisnotarealtask")


def test_DMCC13Benchmark_phase_encodings():
    """Test DMCC13Benchmark DataGrabber invalid phase encodings."""
    with pytest.raises(
        ValueError,
        match=(
            "moonphase is not a valid phase encoding in " "the DMCC dataset"
        ),
    ):
        DMCC13Benchmark(phase_encodings="moonphase")


def test_DMCC13Benchmark_runs():
    """Test DMCC13Benchmark DataGrabber invalid runs."""
    with pytest.raises(
        ValueError,
        match=("cerebralrun is not a valid run in " "the DMCC dataset"),
    ):
        DMCC13Benchmark(runs="cerebralrun")
