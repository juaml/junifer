"""Provide concrete implementation for DMCC13Benchmark DataGrabber."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from enum import Enum
from itertools import product
from typing import Literal

from pydantic import HttpUrl

from ..api.decorators import register_datagrabber
from ..typing import DataGrabberPatterns
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


class DMCCSession(str, Enum):
    """Accepted DMCC sessions."""

    Wave1Bas = "ses-wave1bas"
    Wave1Pro = "ses-wave1pro"
    Wave1Rea = "ses-wave1rea"


class DMCCTask(str, Enum):
    """Accepted DMCC tasks."""

    Rest = "Rest"
    Axcpt = "Axcpt"
    Cuedts = "Cuedts"
    Stern = "Stern"
    Stroop = "Stroop"


class DMCCPhaseEncoding(str, Enum):
    """Accepted DMCC phase encoding directions."""

    AP = "AP"
    PA = "PA"


class DMCCRun(str, Enum):
    """Accepted DMCC runs."""

    One = "1"
    Two = "2"


@register_datagrabber
class DMCC13Benchmark(PatternDataladDataGrabber):
    """Concrete implementation for datalad-based data fetching of DMCC13.

    Parameters
    ----------
    types : list of {``DataType.BOLD``, ``DataType.T1w``, \
            ``DataType.VBM_CSF``, ``DataType.VBM_GM``, ``DataType.VBM_WM``, \
            ``DataType.Warp``}, optional
        The data type(s) to grab.
    datadir : pathlib.Path, optional
        That path where the datalad dataset will be cloned.
        If not specified, the datalad dataset will be cloned into a temporary
        directory.
    sessions : list of :enum:`.DMCCSession`, optional
        DMCC sessions.
        By default, all available sessions are selected.
    tasks : list of :enum:`.DMCCTask`, optional
        DMCC tasks.
        By default, all available tasks are selected.
    phase_encodings : list of :enum:`.DMCCPhaseEncoding`, optional
        DMCC phase encoding directions.
        By default, all available phase encodings are selected.
    runs : list of :enum:`.DMCCRun`, optional
        DMCC runs.
        By default, all available runs are selected.
    native_t1w : bool, optional
        Whether to use T1w in native space (default False).

    """

    uri: HttpUrl = HttpUrl("https://github.com/OpenNeuroDatasets/ds003452.git")
    types: list[
        Literal[
            DataType.BOLD,
            DataType.T1w,
            DataType.VBM_CSF,
            DataType.VBM_GM,
            DataType.VBM_WM,
            DataType.Warp,
        ]
    ] = [  # noqa: RUF012
        DataType.BOLD,
        DataType.T1w,
        DataType.VBM_CSF,
        DataType.VBM_GM,
        DataType.VBM_WM,
    ]
    sessions: list[DMCCSession] = [  # noqa: RUF012
        DMCCSession.Wave1Bas,
        DMCCSession.Wave1Pro,
        DMCCSession.Wave1Rea,
    ]
    tasks: list[DMCCTask] = [  # noqa: RUF012
        DMCCTask.Rest,
        DMCCTask.Axcpt,
        DMCCTask.Cuedts,
        DMCCTask.Stern,
        DMCCTask.Stroop,
    ]
    phase_encodings: list[DMCCPhaseEncoding] = [  # noqa: RUF012
        DMCCPhaseEncoding.AP,
        DMCCPhaseEncoding.PA,
    ]
    runs: list[DMCCRun] = [  # noqa: RUF012
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

    def get_item(
        self,
        subject: str,
        session: str,
        task: str,
        phase_encoding: str,
        run: str,
    ) -> dict:
        """Get the specified item from the dataset.

        Parameters
        ----------
        subject : str
            The subject ID.
        session : {"ses-wave1bas", "ses-wave1pro", "ses-wave1rea"}
            The session to get.
        task : {"Rest", "Axcpt", "Cuedts", "Stern", "Stroop"}
            The task to get.
        phase_encoding : {"AP", "PA"}
            The phase encoding to get.
        run : {"1", "2"}
            The run to get.

        Returns
        -------
        out : dict
            Dictionary of paths for each type of data required for the
            specified element.

        """
        # Format run
        if phase_encoding == "AP":
            run = "1"
        else:
            run = "2"
        # Fetch item
        out = super().get_item(
            subject=subject,
            session=session,
            task=task,
            phase_encoding=phase_encoding,
            run=run,
        )
        return out

    def get_elements(self) -> list:
        """Implement fetching list of subjects in the dataset.

        Returns
        -------
        list of str
            The list of subjects in the dataset.

        """
        subjects = [
            "sub-f1031ax",
            "sub-f1552xo",
            "sub-f1659oa",
            "sub-f1670rz",
            "sub-f1951tt",
            "sub-f3300jh",
            "sub-f3720ca",
            "sub-f5004cr",
            "sub-f5407sl",
            "sub-f5416zj",
            "sub-f8113do",
            "sub-f8570ui",
            "sub-f9057kp",
        ]
        elems = []
        # For wave1bas session
        for subject, session, task, phase_encoding in product(
            subjects,
            ["ses-wave1bas"],
            self.tasks,
            self.phase_encodings,
        ):
            if phase_encoding == "AP":
                run = "1"
            else:
                run = "2"
            # Bypass for f1951tt not having run 2 for Rest
            if subject == "sub-f1951tt" and task == "Rest" and run == "2":
                continue
            elems.append((subject, session, task, phase_encoding, run))
        # For other sessions
        for subject, session, task, phase_encoding in product(
            subjects,
            ["ses-wave1pro", "ses-wave1rea"],
            ["Rest"],
            self.phase_encodings,
        ):
            if phase_encoding == "AP":
                run = "1"
            else:
                run = "2"
            # Bypass for f5416zj for not having wave1rea session
            if subject == "sub-f5416zj" and session == "ses-wave1rea":
                continue
            elems.append((subject, session, task, phase_encoding, run))

        return elems
