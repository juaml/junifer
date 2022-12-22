"""Provide concrete implementations for AOMICPIOP2 data access."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Vera Komeyer <v.komeyer@fz-juelich.de>
#          Xuan Li <xu.li@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import List, Union

from junifer.datagrabber import PatternDataladDataGrabber

from ...api.decorators import register_datagrabber
from ...utils import raise_error


@register_datagrabber
class DataladAOMICPIOP2(PatternDataladDataGrabber):
    """Concrete implementation for pattern-based data fetching of AOMICPIOP2.

    Parameters
    ----------
    datadir : str or Path, optional
        The directory where the datalad dataset will be cloned. If None,
        the datalad dataset will be cloned into a temporary directory
        (default None).
    tasks : {"restingstate", "stopsignal", "emomatching", "workingmemory"} \
            or list of the options, optional
        AOMIC PIOP2 task sessions. If None, all available task sessions are
        selected (default None).
    """

    def __init__(
        self,
        datadir: Union[str, Path, None] = None,
        tasks: Union[str, List[str], None] = None,
    ) -> None:
        # The types of data
        types = [
            "BOLD",
            "BOLD_confounds",
            "T1w",
            "probseg_CSF",
            "probseg_GM",
            "probseg_WM",
            "DWI",
        ]

        if isinstance(tasks, str):
            tasks = [tasks]

        all_tasks = [
            "restingstate",
            "emomatching",
            "workingmemory",
            "stopsignal",
        ]

        if tasks is None:
            tasks = all_tasks
        else:
            for t in tasks:
                if t not in all_tasks:
                    raise_error(
                        f"{t} is not a valid task in the AOMIC PIOP2"
                        " dataset!"
                    )

        self.tasks = tasks

        patterns = {
            "BOLD": (
                "derivatives/fmriprep/sub-{subject}/func/"
                "sub-{subject}_task-{task}_acq-seq_"
                "space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz"
            ),
            "BOLD_confounds": (
                "derivatives/fmriprep/sub-{subject}/func/"
                "sub-{subject}_task-{task}_acq-seq_"
                "desc-confounds_regressors.tsv"
            ),
            "T1w": (
                "derivatives/fmriprep/sub-{subject}/anat/"
                "sub-{subject}_space-MNI152NLin2009cAsym_"
                "desc-preproc_T1w.nii.gz"
            ),
            "probseg_CSF": (
                "derivatives/fmriprep/sub-{subject}/anat/"
                "sub-{subject}_space-MNI152NLin2009cAsym_label-"
                "CSF_probseg.nii.gz"
            ),
            "probseg_GM": (
                "derivatives/fmriprep/sub-{subject}/anat/"
                "sub-{subject}_space-MNI152NLin2009cAsym_label-"
                "GM_probseg.nii.gz"
            ),
            "probseg_WM": (
                "derivatives/fmriprep/sub-{subject}/anat/"
                "sub-{subject}_space-MNI152NLin2009cAsym_label-"
                "WM_probseg.nii.gz"
            ),
            "DWI": (
                "derivatives/dwipreproc/sub-{subject}/dwi/"
                "sub-{subject}_desc-preproc_dwi.nii.gz"
            ),
        }
        uri = "https://github.com/OpenNeuroDatasets/ds002790"
        replacements = ["subject", "task"]
        super().__init__(
            types=types,
            datadir=datadir,
            uri=uri,
            patterns=patterns,
            replacements=replacements,
            confounds_format="fmriprep",
        )

    def get_elements(self) -> List:
        """Implement fetching list of elements in the dataset.

        Returns
        -------
        list
            The list of elements that can be grabbed in the dataset after
            imposing constraints based on specified tasks.
        """
        all_elements = super().get_elements()
        return [x for x in all_elements if x[1] in self.tasks]
