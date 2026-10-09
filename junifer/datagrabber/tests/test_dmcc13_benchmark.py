"""Provide tests for DMCC13Benchmark DataGrabber."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL
from collections.abc import Iterator
from pathlib import Path

import pytest
from pydantic import AnyUrl

from junifer.datagrabber import DataType, DMCC13Benchmark
from junifer.testing import config_override


URI = AnyUrl(
    "https://cerebra.fz-juelich.de/junifer/datalad-example-dmcc13-benchmark.git"
)


@pytest.fixture(scope="module")
def dmcc13_datadir(tmp_path_factory) -> Iterator[Path]:
    """Return the path to the DMCC13 benchmark data directory.

    Parameters
    ----------
    tmp_path_factory : pathlib.Path
        The path to the test directory.

    Returns
    -------
    pathlib.Path
        The path to the DMCC13 benchmark data directory.

    """
    datadir = tmp_path_factory.mktemp("dmcc13_datadir")
    datadir.mkdir(parents=True, exist_ok=True)
    dg = DMCC13Benchmark(uri=URI, types=["T1w"], datadir=datadir)
    with config_override("datagrabber.skipidcheck", True), dg:
        yield datadir


@pytest.mark.parametrize(
    "sessions, tasks, phase_encodings, runs, native_t1w",
    [
        (["ses-wave1bas"], ["Rest"], ["AP"], ["1"], False),
        (["ses-wave1bas"], ["Axcpt"], ["AP"], ["1"], False),
        (["ses-wave1bas"], ["Cuedts"], ["AP"], ["1"], False),
        (["ses-wave1bas"], ["Stern"], ["AP"], ["1"], False),
        (["ses-wave1bas"], ["Stroop"], ["AP"], ["1"], False),
        (["ses-wave1bas"], ["Rest"], ["PA"], ["2"], False),
        (["ses-wave1bas"], ["Axcpt"], ["PA"], ["2"], False),
        (["ses-wave1bas"], ["Cuedts"], ["PA"], ["2"], False),
        (["ses-wave1bas"], ["Stern"], ["PA"], ["2"], False),
        (["ses-wave1bas"], ["Stroop"], ["PA"], ["2"], False),
        (["ses-wave1bas"], ["Rest"], ["AP"], ["1"], True),
        (["ses-wave1bas"], ["Axcpt"], ["AP"], ["1"], True),
        (["ses-wave1bas"], ["Cuedts"], ["AP"], ["1"], True),
        (["ses-wave1bas"], ["Stern"], ["AP"], ["1"], True),
        (["ses-wave1bas"], ["Stroop"], ["AP"], ["1"], True),
        (["ses-wave1bas"], ["Rest"], ["PA"], ["2"], True),
        (["ses-wave1bas"], ["Axcpt"], ["PA"], ["2"], True),
        (["ses-wave1bas"], ["Cuedts"], ["PA"], ["2"], True),
        (["ses-wave1bas"], ["Stern"], ["PA"], ["2"], True),
        (["ses-wave1bas"], ["Stroop"], ["PA"], ["2"], True),
        (["ses-wave1pro"], ["Rest"], ["AP"], ["1"], False),
        (["ses-wave1pro"], ["Rest"], ["PA"], ["2"], False),
        (["ses-wave1pro"], ["Rest"], ["AP"], ["1"], True),
        (["ses-wave1pro"], ["Rest"], ["PA"], ["2"], True),
        (["ses-wave1rea"], ["Rest"], ["AP"], ["1"], False),
        (["ses-wave1rea"], ["Rest"], ["PA"], ["2"], False),
        (["ses-wave1rea"], ["Rest"], ["AP"], ["1"], True),
        (["ses-wave1rea"], ["Rest"], ["PA"], ["2"], True),
    ],
)
def test_DMCC13Benchmark(
    sessions: list[str],
    tasks: list[str],
    phase_encodings: list[str],
    runs: list[str],
    native_t1w: bool,
    dmcc13_datadir: Path,
) -> None:
    """Test DMCC13Benchmark DataGrabber.

    Parameters
    ----------
    sessions : list of str
        The parametrized session values.
    tasks : list of str
        The parametrized task values.
    phase_encodings : list of str
        The parametrized phase encoding values.
    runs : list of str
        The parametrized run values.
    native_t1w : bool
        The parametrized values for fetching native T1w.
    dmcc13_datadir : pathlib.Path
        The path to the DMCC13 benchmark data directory.

    """
    dg = DMCC13Benchmark(
        uri=URI,
        sessions=sessions,
        tasks=tasks,
        phase_encodings=phase_encodings,
        runs=runs,
        native_t1w=native_t1w,
        datadir=dmcc13_datadir,
    )
    with dg:
        all_elements = dg.get_elements()
        test_element = all_elements[0]
        _, ses, task, phase, run = test_element
        out = dg[("sub-01", ses, task, phase, run)]

        # Available data types
        data_types = [
            DataType.BOLD,
            DataType.VBM_CSF,
            DataType.VBM_GM,
            DataType.VBM_WM,
            DataType.T1w,
        ]
        # Add Warp if native T1w is accessed
        if native_t1w:
            data_types.append(DataType.Warp)

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

        for data_type, data_file_name in zip(
            data_types, data_file_names, strict=False
        ):
            # Assert data type
            assert data_type in out.keys()
            # Conditional for Warp
            if data_type is DataType.Warp:
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
            strict=False,
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
        (["BOLD"], True),
        ("BOLD", False),
        (["T1w"], True),
        ("T1w", False),
        (["VBM_CSF"], True),
        ("VBM_CSF", False),
        (["VBM_GM"], True),
        ("VBM_GM", False),
        (["VBM_WM"], True),
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
    types: str | list[str],
    native_t1w: bool,
    dmcc13_datadir: Path,
) -> None:
    """Test DMCC13Benchmark DataGrabber partial data access.

    Parameters
    ----------
    types : str or list of str
        The parametrized types.
    native_t1w : bool
        The parametrized values for fetching native T1w.
    dmcc13_datadir : pathlib.Path
        The path to the DMCC13 benchmark data directory.

    """
    dg = DMCC13Benchmark(
        uri=URI,
        types=types,
        native_t1w=native_t1w,
        datadir=dmcc13_datadir,
    )
    with dg:
        all_elements = dg.get_elements()
        test_element = all_elements[0]
        # Elements only have the subject if no data type of the tasks is
        # grabbed
        if isinstance(test_element, tuple):
            out = dg[("sub-01", *test_element[1:])]
        else:
            out = dg["sub-01"]
        # Assert data type
        if isinstance(types, str):
            types = [types]
        for type_ in types:
            assert type_ in out
            element = out[type_]["meta"]["element"]
            assert list(element) == dg.get_element_keys()
