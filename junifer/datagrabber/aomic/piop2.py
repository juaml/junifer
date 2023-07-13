"""Provide concrete implementation for AOMIC PIOP2 DataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Vera Komeyer <v.komeyer@fz-juelich.de>
#          Xuan Li <xu.li@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import Dict, List, Union

from ...api.decorators import register_datagrabber
from ...utils import raise_error
from ..pattern_datalad import PatternDataladDataGrabber


@register_datagrabber
class DataladAOMICPIOP2(PatternDataladDataGrabber):
    """Concrete implementation for pattern-based data fetching of AOMIC PIOP2.

    Parameters
    ----------
    datadir : str or Path or None, optional
        The directory where the datalad dataset will be cloned. If None,
        the datalad dataset will be cloned into a temporary directory
        (default None).
    types: {"BOLD", "BOLD_confounds", "T1w", "probseg_CSF", "probseg_GM", \
           "probseg_WM", "DWI"} or a list of the options, optional
        AOMIC data types. If None, all available data types are selected.
        (default None).
    tasks : {"restingstate", "stopsignal", "emomatching", "workingmemory"} \
            or list of the options, optional
        AOMIC PIOP2 task sessions. If None, all available task sessions are
        selected (default None).

    """

    def __init__(
        self,
        datadir: Union[str, Path, None] = None,
        types: Union[str, List[str], None] = None,
        tasks: Union[str, List[str], None] = None,
    ) -> None:
        # Declare all tasks
        all_tasks = [
            "restingstate",
            "anticipation",
            "emomatching",
            "faces",
            "gstroop",
            "workingmemory",
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
                    raise_error(
                        f"{t} is not a valid task in the AOMIC PIOP2"
                        " dataset!"
                    )
        self.tasks = tasks
        # The patterns
        patterns = {
            "BOLD": (
                "derivatives/fmriprep/sub-{subject}/func/"
                "sub-{subject}_task-{task}_"
                "space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz"
            ),
            "BOLD_confounds": (
                "derivatives/fmriprep/sub-{subject}/func/"
                "sub-{subject}_task-{task}_"
                "desc-confounds_regressors.tsv"
            ),
            "BOLD_mask": (
                "derivatives/fmriprep/sub-{subject}/func/"
                "sub-{subject}_task-{task}_"
                "space-MNI152NLin2009cAsym_desc-brain_mask.nii.gz"
            ),
            "T1w": (
                "derivatives/fmriprep/sub-{subject}/anat/"
                "sub-{subject}_space-MNI152NLin2009cAsym_"
                "desc-preproc_T1w.nii.gz"
            ),
            "T1w_mask": (
                "derivatives/fmriprep/sub-{subject}/anat/"
                "sub-{subject}_space-MNI152NLin2009cAsym_"
                "desc-brain_mask.nii.gz"
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
        # Set default types
        if types is None:
            types = list(patterns.keys())
        # Convert single type into list
        else:
            if not isinstance(types, list):
                types = [types]
        # The replacements
        replacements = ["subject", "task"]
        uri = "https://github.com/OpenNeuroDatasets/ds002790"
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

    def get_item(self, subject: str, task: str) -> Dict:
        """Index one element in the dataset.

        Parameters
        ----------
        subject : str
            The subject ID.
        task : str
            The task to get. Possible values are:
            {"restingstate", "stopsignal", "emomatching", "workingmemory"}

        Returns
        -------
        out : dict
            Dictionary of paths for each type of data required for the
            specified element.

        """
        out = super().get_item(subject=subject, task=task)
        out["BOLD"]["mask_item"] = "BOLD_mask"
        out["T1w"]["mask_item"] = "T1w_mask"
        return out
