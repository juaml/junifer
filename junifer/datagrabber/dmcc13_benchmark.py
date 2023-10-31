"""Provide concrete implementation for DMCC13Benchmark DataGrabber."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from itertools import product
from pathlib import Path
from typing import Dict, List, Union

from ..api.decorators import register_datagrabber
from ..utils import raise_error
from .pattern_datalad import PatternDataladDataGrabber


__all__ = ["DMCC13Benchmark"]


@register_datagrabber
class DMCC13Benchmark(PatternDataladDataGrabber):
    """Concrete implementation for datalad-based data fetching of DMCC13.

    Parameters
    ----------
    datadir : str or Path or None, optional
        The directory where the datalad dataset will be cloned. If None,
        the datalad dataset will be cloned into a temporary directory
        (default None).
    types: {"BOLD", "BOLD_confounds", "T1w", "probseg_CSF", "probseg_GM", \
           "probseg_WM"} or a list of the options, optional
        DMCC data types. If None, all available data types are selected.
        (default None).
    sessions: {"wave1bas", "wave1pro", "wave1rea"} or list of the options, \
               optional
        DMCC sessions. If None, all available sessions are selected
        (default None).
    tasks: {"Rest", "Axcpt", "Cuedts", "Stern", "Stroop"} or \
            list of the options, optional
        DMCC task sessions. If None, all available task sessions are selected
        (default None).
    phase_encodings : {"AP", "PA"} or list of the options, optional
        DMCC phase encoding directions. If None, all available phase encodings
        are selected (default None).
    runs : {"1", "2"} or list of the options, optional
        DMCC runs. If None, all available runs are selected (default None).
    native_t1w : bool, optional
        Whether to use T1w in native space (default False).

    Raises
    ------
    ValueError
        If invalid value is passed for:
         * ``sessions``
         * ``tasks``
         * ``phase_encodings``
         * ``runs``

    """

    def __init__(
        self,
        datadir: Union[str, Path, None] = None,
        types: Union[str, List[str], None] = None,
        sessions: Union[str, List[str], None] = None,
        tasks: Union[str, List[str], None] = None,
        phase_encodings: Union[str, List[str], None] = None,
        runs: Union[str, List[str], None] = None,
        native_t1w: bool = False,
    ) -> None:
        # Declare all sessions
        all_sessions = [
            "wave1bas",
            "wave1pro",
            "wave1rea",
        ]
        # Set default sessions
        if sessions is None:
            sessions = all_sessions
        else:
            # Convert single session into list
            if isinstance(sessions, str):
                sessions = [sessions]
            # Verify valid sessions
            for s in sessions:
                if s not in all_sessions:
                    raise_error(
                        f"{s} is not a valid session in the DMCC dataset"
                    )
        self.sessions = sessions
        # Declare all tasks
        all_tasks = [
            "Rest",
            "Axcpt",
            "Cuedts",
            "Stern",
            "Stroop",
        ]
        # Set default tasks
        if tasks is None:
            tasks = all_tasks
        else:
            # Convert single task into list
            if isinstance(tasks, str):
                tasks = [tasks]
            # Verify valid tasks
            for t in tasks:
                if t not in all_tasks:
                    raise_error(f"{t} is not a valid task in the DMCC dataset")
        self.tasks = tasks
        # Declare all phase encodings
        all_phase_encodings = ["AP", "PA"]
        # Set default phase encodings
        if phase_encodings is None:
            phase_encodings = all_phase_encodings
        else:
            # Convert single phase encoding into list
            if isinstance(phase_encodings, str):
                phase_encodings = [phase_encodings]
            # Verify valid phase encodings
            for p in phase_encodings:
                if p not in all_phase_encodings:
                    raise_error(
                        f"{p} is not a valid phase encoding in the DMCC "
                        "dataset"
                    )
        self.phase_encodings = phase_encodings
        # Declare all runs
        all_runs = ["1", "2"]
        # Set default runs
        if runs is None:
            runs = all_runs
        else:
            # Convert single run into list
            if isinstance(runs, str):
                runs = [runs]
            # Verify valid runs
            for r in runs:
                if r not in all_runs:
                    raise_error(f"{r} is not a valid run in the DMCC dataset")
        self.runs = runs
        # The patterns
        patterns = {
            "BOLD": (
                "derivatives/fmriprep-1.3.2/sub-{subject}/ses-{session}/"
                "func/sub-{subject}_ses-{session}_task-{task}_acq-mb4"
                "{phase_encoding}_run-{run}_"
                "space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz"
            ),
            "BOLD_confounds": (
                "derivatives/fmriprep-1.3.2/sub-{subject}/ses-{session}/"
                "func/sub-{subject}_ses-{session}_task-{task}_acq-mb4"
                "{phase_encoding}_run-{run}_desc-confounds_regressors.tsv"
            ),
            "BOLD_mask": (
                "derivatives/fmriprep-1.3.2/sub-{subject}/ses-{session}/"
                "/func/sub-{subject}_ses-{session}_task-{task}_acq-mb4"
                "{phase_encoding}_run-{run}_"
                "space-MNI152NLin2009cAsym_desc-brain_mask.nii.gz"
            ),
            "T1w": (
                "derivatives/fmriprep-1.3.2/sub-{subject}/anat/"
                "sub-{subject}_space-MNI152NLin2009cAsym_desc-preproc_T1w.nii.gz"
            ),
            "T1w_mask": (
                "derivatives/fmriprep-1.3.2/sub-{subject}/anat/"
                "sub-{subject}_space-MNI152NLin2009cAsym_desc-brain_mask.nii.gz"
            ),
            "probseg_CSF": (
                "derivatives/fmriprep-1.3.2/sub-{subject}/anat/"
                "sub-{subject}_space-MNI152NLin2009cAsym_label-CSF_probseg.nii.gz"
            ),
            "probseg_GM": (
                "derivatives/fmriprep-1.3.2/sub-{subject}/anat/"
                "sub-{subject}_space-MNI152NLin2009cAsym_label-GM_probseg.nii.gz"
            ),
            "probseg_WM": (
                "derivatives/fmriprep-1.3.2/sub-{subject}/anat/"
                "sub-{subject}_space-MNI152NLin2009cAsym_label-WM_probseg.nii.gz"
            ),
        }
        # Use native T1w assets
        self.native_t1w = False
        if native_t1w:
            self.native_t1w = True
            patterns.update(
                {
                    "T1w": (
                        "derivatives/fmriprep-1.3.2/sub-{subject}/anat/"
                        "sub-{subject}_desc-preproc_T1w.nii.gz"
                    ),
                    "T1w_mask": (
                        "derivatives/fmriprep-1.3.2/sub-{subject}/anat/"
                        "sub-{subject}_desc-brain_mask.nii.gz"
                    ),
                    "Warp": (
                        "derivatives/fmriprep-1.3.2/sub-{subject}/anat/"
                        "sub-{subject}_from-MNI152NLin2009cAsym_to-T1w_"
                        "mode-image_xfm.h5"
                    ),
                }
            )
        # Set default types
        if types is None:
            types = list(patterns.keys())
        # Convert single type into list
        else:
            if not isinstance(types, list):
                types = [types]
        # The replacements
        replacements = ["subject", "session", "task", "phase_encoding", "run"]
        uri = "https://github.com/OpenNeuroDatasets/ds003452.git"
        super().__init__(
            types=types,
            datadir=datadir,
            uri=uri,
            patterns=patterns,
            replacements=replacements,
            confounds_format="fmriprep",
        )

    def get_item(
        self,
        subject: str,
        session: str,
        task: str,
        phase_encoding: str,
        run: str,
    ) -> Dict:
        """Index one element in the dataset.

        Parameters
        ----------
        subject : str
            The subject ID.
        session : {"wave1bas", "wave1pro", "wave1rea"}
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
        if out.get("BOLD"):
            out["BOLD"]["mask_item"] = "BOLD_mask"
            # Add space information
            out["BOLD"].update({"space": "MNI152NLin2009cAsym"})
        if out.get("T1w"):
            out["T1w"]["mask_item"] = "T1w_mask"
            # Add space information
            if self.native_t1w:
                out["T1w"].update({"space": "native"})
            else:
                out["T1w"].update({"space": "MNI152NLin2009cAsym"})
        return out

    def get_elements(self) -> List:
        """Implement fetching list of subjects in the dataset.

        Returns
        -------
        list of str
            The list of subjects in the dataset.

        """
        subjects = [
            "f1031ax",
            "f1552xo",
            "f1659oa",
            "f1670rz",
            "f1951tt",
            "f3300jh",
            "f3720ca",
            "f5004cr",
            "f5407sl",
            "f5416zj",
            "F8113do",
            "f8570ui",
            "f9057kp",
        ]
        elems = []
        # For wave1bas session
        for subject, session, task, phase_encoding in product(
            subjects,
            ["wave1bas"],
            self.tasks,
            self.phase_encodings,
        ):
            if phase_encoding == "AP":
                run = "1"
            else:
                run = "2"
            # Bypass for f1951tt not having run 2 for Rest
            if subject == "f1951tt" and task == "Rest" and run == "2":
                continue
            elems.append((subject, session, task, phase_encoding, run))
        # For other sessions
        for subject, session, task, phase_encoding in product(
            subjects,
            ["wave1pro", "wave1rea"],
            ["Rest"],
            self.phase_encodings,
        ):
            if phase_encoding == "AP":
                run = "1"
            else:
                run = "2"
            elems.append((subject, session, task, phase_encoding, run))

        return elems
