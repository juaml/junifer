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
from ....datagrabber.utils import validate_and_format_parameters


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
            "probseg_GM": (
                "fmriprep/sub-{subject}/anat/"
                "sub-{subject}_label-GM_probseg.nii.gz"
            ),
            "probseg_WM": (
                "fmriprep/sub-{subject}/anat/"
                "sub-{subject}_label-WM_probseg.nii.gz"
            ),
            "probseg_CSF": (
                "fmriprep/sub-{subject}/anat/"
                "sub-{subject}_label-CSF_probseg.nii.gz"
            ),
        }
        types = list(patterns.keys())

        replacements = ["subject", "session", "task", "TR"]

        # all TRs
        all_TRs = ["645", "1400", "cap"]

        # configure and validate parameters
        param_list = []
        descs = ["session", "task", "TR"]
        valid_params = [all_sessions, all_tasks, all_TRs]
        given_params = [sessions, tasks, TRs]
        for given_param, valid_param, desc in zip(
            given_params, valid_params, descs
        ):
            error_msg = (
                f"Invalid eNKI datagrabber {desc}. "
                f"Valid values can be any or all of {valid_params}."
            )
            param_list.append(
                validate_and_format_parameters(
                    given_param, valid_param, error_msg
                )
            )
        sessions, tasks, TRs = param_list

        super().__init__(
            types=types,
            datadir=datadir,
            replacements=replacements,
            patterns=patterns,
        )
