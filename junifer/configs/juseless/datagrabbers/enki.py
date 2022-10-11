"""Provide class for eNKI juseless datagrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Vera Komeyer <v.komeyer@fz-juelich.de>
#          Xuan Li <xu.li@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import List, Union

from ....api.decorators import register_datagrabber
from ....datagrabber import PatternDataGrabber
from ....utils import raise_error


@register_datagrabber
class JuselesseNKI(PatternDataGrabber):
    """Juseless eNKI DataGrabber class.

    Implements a DataGrabber to access the eNKI data in Juseless.

    Parameters
    -----------
    datadir : str or pathlib.Path, optional
        The directory containing the eNKI data.
        (default '/data/project/enki/processed/')
    sessions : {"ALGA", "ALGAF", "CLG2", "CLG2R", "CLG4", "CLG4R", "CLG5",
        "CLGA", "DS2", "DS2A", "DSA", "NFB2", "NFB2R", "NFB3", "NFBA", "NFBAR"}
        or list of the options, optional eNKI sessions.
        If None, all available sessions are selected.
        (default None).
    tasks : {"rest", "visual_checkerboard", "breathhold"} or list of the
        options, optional eNKI tasks.
        If None, all available tasks are selected
        (default None).
    TRs : {"645", "1400", "cap"} or list of the options, optional
        eNKI Repetition Times (TRs). If None, all three will be used
        (default None).
    **kwargs
        Keyword arguments passed to superclass.
    """

    def __init__(
        self,
        datadir: Union[str, Path, None] = "/data/project/enki/processed",
        sessions: Union[str, List[str], None] = None,
        tasks: Union[str, List[str], None] = None,
        TRs: Union[str, List[str], None] = None,
    ) -> None:
        """Initialize the class."""

        types = ["T1w", "BOLD", "BOLD_confounds"]

        # All sessions
        all_sessions = [
            "ALGA",
            "ALGAF",
            "CLG2",
            "CLG2R",
            "CLG4",
            "CLG4R",
            "CLG5",
            "CLGA",
            "DS2",
            "DS2A",
            "DSA",
            "NFB2",
            "NFB2R",
            "NFB3",
            "NFBA",
            "NFBAR",
        ]
        # All tasks
        all_tasks = [
            "rest",
            "visual_checkerboard",
            "breathhold",
        ]

        patterns = {
            "T1w": (
                "fmriprep/sub-{subject}/"
                "anat/sub-{subject}_desc-preproc_T1w.nii.gz"
            ),
            "BOLD": (
                "fmriprep/sub-{subject}/ses-{session}/func/"
                "sub-{subject}_ses-{session}_task-{task}_acq"
                "-{TR}_space-MNI152NLin6Asym_desc-preproc_bold.nii.gz"
            ),
            "BOLD_confounds": (
                "fmriprep/sub-{subject}/ses-{session}/func/"
                "sub-{subject}_ses-{session}_task-{task}_acq-"
                "{TR}_desc-confounds_regressors.tsv"
            ),
        }

        replacements = ["subject", "session", "task", "TR"]

        # all TRs
        all_TRs = ["645", "1400", "cap"]

        # configure and validate sessions
        if sessions is None:
            sessions = all_sessions
        else:
            if isinstance(sessions, str):
                sessions = [sessions]
            for s in sessions:
                if s not in all_sessions:
                    raise_error(
                        f"{s} is not a valid session in the eNKI"
                        " dataset! Valid session values can be any or "
                        f"all of {all_sessions}."
                    )

        # configure and validate tasks
        if tasks is None:
            tasks = all_tasks
        # Convert single task into list
        else:
            if not isinstance(tasks, List):
                tasks = [tasks]
            # Check for invalid task(s)
            for task in tasks:
                if task not in all_tasks:
                    raise_error(
                        f"'{task}' is not a valid eNKI fMRI task input. "
                        f"Valid task values can be any or all of {all_tasks}."
                    )

        # configure and validate TRs
        if TRs is None:
            TRs = all_TRs
        # Convert single TR into list
        else:
            if isinstance(TRs, str):
                TRs = [TRs]
            # Check for invalid TR(s)
            for tr in TRs:
                if tr not in all_TRs:
                    raise_error(
                        f"'{tr}' is not a valid eNKI TR. "
                        "Valid repition times (TRs) can be any or all of "
                        f"{all_TRs}."
                    )

        super().__init__(
            types=types,
            datadir=datadir,
            replacements=replacements,
            patterns=patterns,
        )
