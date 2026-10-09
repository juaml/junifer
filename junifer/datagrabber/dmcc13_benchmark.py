"""Provide concrete implementation for DMCC13Benchmark DataGrabber."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from enum import StrEnum
from typing import Annotated, ClassVar, Literal

from pydantic import AnyUrl, BeforeValidator

from ..api.decorators import register_datagrabber
from ..typing import DataGrabberPatterns
from ..utils import ensure_list
from .base import DataType
from .pattern import ConfoundsFormat
from .pattern_datalad import PatternDataladDataGrabber


__all__ = [
    "DMCC13Benchmark",
    "DMCCPhaseEncoding",
    "DMCCRun",
    "DMCCSession",
    "DMCCTask",
]


class DMCCSession(StrEnum):
    """Accepted DMCC sessions."""

    Wave1Bas = "ses-wave1bas"
    Wave1Pro = "ses-wave1pro"
    Wave1Rea = "ses-wave1rea"


class DMCCTask(StrEnum):
    """Accepted DMCC tasks."""

    Rest = "Rest"
    Axcpt = "Axcpt"
    Cuedts = "Cuedts"
    Stern = "Stern"
    Stroop = "Stroop"


class DMCCPhaseEncoding(StrEnum):
    """Accepted DMCC phase encoding directions."""

    AP = "AP"
    PA = "PA"


class DMCCRun(StrEnum):
    """Accepted DMCC runs."""

    One = "1"
    Two = "2"


_types = Literal[
    DataType.BOLD,
    DataType.T1w,
    DataType.VBM_CSF,
    DataType.VBM_GM,
    DataType.VBM_WM,
    DataType.Warp,
]

_sessions = Literal[
    DMCCSession.Wave1Bas,
    DMCCSession.Wave1Pro,
    DMCCSession.Wave1Rea,
]

_tasks = Literal[
    DMCCTask.Rest,
    DMCCTask.Axcpt,
    DMCCTask.Cuedts,
    DMCCTask.Stern,
    DMCCTask.Stroop,
]

_phase_encodings = Literal[
    DMCCPhaseEncoding.AP,
    DMCCPhaseEncoding.PA,
]

_runs = Literal[
    DMCCRun.One,
    DMCCRun.Two,
]


@register_datagrabber
class DMCC13Benchmark(PatternDataladDataGrabber):
    """Concrete implementation for datalad-based data fetching of DMCC13.

    Parameters
    ----------
    types : {"BOLD", "T1w", "VBM_CSF", "VBM_GM", "VBM_WM", "Warp"} or \
            list of the options, optional
        The data type(s) to grab.
    datadir : pathlib.Path, optional
        That path where the datalad dataset will be cloned.
        If not specified, the datalad dataset will be cloned into a temporary
        directory.
    sessions : {"ses-wave1bas", "ses-wave1pro", "ses-wave1rea"} or \
               list of the options, optional
        DMCC sessions.
        By default, all available sessions are selected.
    tasks : {"Rest", "Axcpt", "Cuedts", "Stern", "Stroop"} or \
            list of the options, optional
        DMCC tasks.
        By default, all available tasks are selected.
    phase_encodings : {"AP", "PA"} or list of the options, optional
        DMCC phase encoding directions.
        By default, all available phase encodings are selected.
    runs : {"1", "2"} or list of the options, optional
        DMCC runs.
        By default, all available runs are selected.
    native_t1w : bool, optional
        Whether to use T1w in native space (default False).

    """

    uri: AnyUrl = AnyUrl("https://github.com/OpenNeuroDatasets/ds003452.git")
    types: Annotated[_types | list[_types], BeforeValidator(ensure_list)] = [  # noqa: RUF012
        DataType.BOLD,
        DataType.T1w,
        DataType.VBM_CSF,
        DataType.VBM_GM,
        DataType.VBM_WM,
    ]
    sessions: Annotated[
        _sessions | list[_sessions], BeforeValidator(ensure_list)
    ] = [  # noqa: RUF012
        DMCCSession.Wave1Bas,
        DMCCSession.Wave1Pro,
        DMCCSession.Wave1Rea,
    ]
    tasks: Annotated[_tasks | list[_tasks], BeforeValidator(ensure_list)] = [  # noqa: RUF012
        DMCCTask.Rest,
        DMCCTask.Axcpt,
        DMCCTask.Cuedts,
        DMCCTask.Stern,
        DMCCTask.Stroop,
    ]
    phase_encodings: Annotated[
        _phase_encodings | list[_phase_encodings],
        BeforeValidator(ensure_list),
    ] = [  # noqa: RUF012
        DMCCPhaseEncoding.AP,
        DMCCPhaseEncoding.PA,
    ]
    runs: Annotated[_runs | list[_runs], BeforeValidator(ensure_list)] = [  # noqa: RUF012
        DMCCRun.One,
        DMCCRun.Two,
    ]
    native_t1w: bool = False
    patterns: DataGrabberPatterns = {  # noqa: RUF012
        "BOLD": {
            "pattern": (
                "derivatives/fmriprep-1.3.2/{subject}/{session}/"
                "func/{subject}_{session}_task-{task}_acq-mb4"
                "{phase_encoding}_run-{run}_"
                "space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz"
            ),
            "space": "MNI152NLin2009cAsym",
            "mask": {
                "pattern": (
                    "derivatives/fmriprep-1.3.2/{subject}/{session}/"
                    "func/{subject}_{session}_task-{task}_acq-mb4"
                    "{phase_encoding}_run-{run}_"
                    "space-MNI152NLin2009cAsym_desc-brain_mask.nii.gz"
                ),
                "space": "MNI152NLin2009cAsym",
            },
            "confounds": {
                "pattern": (
                    "derivatives/fmriprep-1.3.2/{subject}/{session}/"
                    "func/{subject}_{session}_task-{task}_acq-mb4"
                    "{phase_encoding}_run-{run}_desc-confounds_regressors.tsv"
                ),
                "format": "fmriprep",
            },
        },
        "T1w": {
            "pattern": (
                "derivatives/fmriprep-1.3.2/{subject}/anat/"
                "{subject}_space-MNI152NLin2009cAsym_desc-preproc_T1w.nii.gz"
            ),
            "space": "MNI152NLin2009cAsym",
            "mask": {
                "pattern": (
                    "derivatives/fmriprep-1.3.2/{subject}/anat/"
                    "{subject}_space-MNI152NLin2009cAsym_desc-brain_mask.nii.gz"
                ),
                "space": "MNI152NLin2009cAsym",
            },
        },
        "VBM_CSF": {
            "pattern": (
                "derivatives/fmriprep-1.3.2/{subject}/anat/"
                "{subject}_space-MNI152NLin2009cAsym_label-CSF_probseg.nii.gz"
            ),
            "space": "MNI152NLin2009cAsym",
        },
        "VBM_GM": {
            "pattern": (
                "derivatives/fmriprep-1.3.2/{subject}/anat/"
                "{subject}_space-MNI152NLin2009cAsym_label-GM_probseg.nii.gz"
            ),
            "space": "MNI152NLin2009cAsym",
        },
        "VBM_WM": {
            "pattern": (
                "derivatives/fmriprep-1.3.2/{subject}/anat/"
                "{subject}_space-MNI152NLin2009cAsym_label-WM_probseg.nii.gz"
            ),
            "space": "MNI152NLin2009cAsym",
        },
    }
    replacements: list[str] = [  # noqa: RUF012
        "subject",
        "session",
        "task",
        "phase_encoding",
        "run",
    ]
    # Only grab the specified sessions, tasks, phase encodings and runs
    _REPLACEMENT_FIELDS: ClassVar[dict[str, str]] = {
        "session": "sessions",
        "task": "tasks",
        "phase_encoding": "phase_encodings",
        "run": "runs",
    }
    confounds_format: ConfoundsFormat = ConfoundsFormat.FMRIPrep

    def validate_datagrabber_params(self) -> None:
        """Run extra logical validation for datagrabber."""
        if self.native_t1w:
            self.patterns.update(
                {
                    "T1w": {
                        "pattern": (
                            "derivatives/fmriprep-1.3.2/{subject}/anat/"
                            "{subject}_desc-preproc_T1w.nii.gz"
                        ),
                        "space": "native",
                        "mask": {
                            "pattern": (
                                "derivatives/fmriprep-1.3.2/{subject}/anat/"
                                "{subject}_desc-brain_mask.nii.gz"
                            ),
                            "space": "native",
                        },
                    },
                    "Warp": [
                        {
                            "pattern": (
                                "derivatives/fmriprep-1.3.2/{subject}/anat/"
                                "{subject}_from-MNI152NLin2009cAsym_to-T1w_"
                                "mode-image_xfm.h5"
                            ),
                            "src": "MNI152NLin2009cAsym",
                            "dst": "native",
                            "warper": "ants",
                        },
                        {
                            "pattern": (
                                "derivatives/fmriprep-1.3.2/{subject}/anat/"
                                "{subject}_from-T1w_to-MNI152NLin2009cAsym_"
                                "mode-image_xfm.h5"
                            ),
                            "src": "native",
                            "dst": "MNI152NLin2009cAsym",
                            "warper": "ants",
                        },
                    ],
                }
            )
            self.types.append(DataType.Warp)
        super().validate_datagrabber_params()
