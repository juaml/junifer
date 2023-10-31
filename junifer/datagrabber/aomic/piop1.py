"""Provide concrete implementation for AOMIC PIOP1 DataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Vera Komeyer <v.komeyer@fz-juelich.de>
#          Xuan Li <xu.li@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from itertools import product
from pathlib import Path
from typing import Dict, List, Union

from ...api.decorators import register_datagrabber
from ...utils import raise_error
from ..pattern_datalad import PatternDataladDataGrabber


@register_datagrabber
class DataladAOMICPIOP1(PatternDataladDataGrabber):
    """Concrete implementation for pattern-based data fetching of AOMIC PIOP1.

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
    tasks : {"restingstate", "anticipation", "emomatching", "faces", \
            "gstroop", "workingmemory"} or list of the options, optional
        AOMIC PIOP1 task sessions. If None, all available task sessions are
        selected (default None).
    native_t1w : bool, optional
        Whether to use T1w in native space (default False).

    Raises
    ------
    ValueError
        If invalid value is passed for ``tasks``.

    """

    def __init__(
        self,
        datadir: Union[str, Path, None] = None,
        types: Union[str, List[str], None] = None,
        tasks: Union[str, List[str], None] = None,
        native_t1w: bool = False,
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
                        f"{t} is not a valid task in the AOMIC PIOP1"
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
        # Use native T1w assets
        self.native_t1w = False
        if native_t1w:
            self.native_t1w = True
            patterns.update(
                {
                    "T1w": (
                        "derivatives/fmriprep/sub-{subject}/anat/"
                        "sub-{subject}_desc-preproc_T1w.nii.gz"
                    ),
                    "T1w_mask": (
                        "derivatives/fmriprep/sub-{subject}/anat/"
                        "sub-{subject}_desc-brain_mask.nii.gz"
                    ),
                    "Warp": (
                        "derivatives/fmriprep/sub-{subject}/anat/"
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
        replacements = ["subject", "task"]
        uri = "https://github.com/OpenNeuroDatasets/ds002785"
        super().__init__(
            types=types,
            datadir=datadir,
            uri=uri,
            patterns=patterns,
            replacements=replacements,
            confounds_format="fmriprep",
        )

    def get_item(self, subject: str, task: str) -> Dict:
        """Index one element in the dataset.

        Parameters
        ----------
        subject : str
            The subject ID.
        task : {"restingstate", "anticipation", "emomatching", "faces", \
                "gstroop", "workingmemory"}
            The task to get.

        Returns
        -------
        out : dict
            Dictionary of paths for each type of data required for the
            specified element.

        """

        task_acqs = {
            "anticipation": "seq",
            "emomatching": "seq",
            "faces": "mb3",
            "gstroop": "seq",
            "restingstate": "mb3",
            "workingmemory": "seq",
        }
        acq = task_acqs[task]
        new_task = f"{task}_acq-{acq}"

        out = super().get_item(subject=subject, task=new_task)
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
        subjects = [f"{x:04d}" for x in range(1, 217)]
        elems = []
        for subject, task in product(subjects, self.tasks):
            elems.append((subject, task))

        return elems
