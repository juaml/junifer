"""Provide concrete implementation for AOMIC PIOP1 DataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Vera Komeyer <v.komeyer@fz-juelich.de>
#          Xuan Li <xu.li@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from itertools import product
from typing import Annotated, Literal, Union

from pydantic import BeforeValidator, HttpUrl

from ...api.decorators import register_datagrabber
from ...typing import DataGrabberPatterns
from ...utils import ensure_list
from ..base import DataType
from ..pattern import ConfoundsFormat
from ..pattern_datalad import PatternDataladDataGrabber
from ._types import AOMICSpace, AOMICTask


__all__ = ["DataladAOMICPIOP1"]

_types = Literal[
    DataType.BOLD,
    DataType.T1w,
    DataType.VBM_CSF,
    DataType.VBM_GM,
    DataType.VBM_WM,
    DataType.DWI,
    DataType.FreeSurfer,
    DataType.Warp,
]

_tasks = Literal[
    AOMICTask.RestingState,
    AOMICTask.Anticipation,
    AOMICTask.EmoMatching,
    AOMICTask.Faces,
    AOMICTask.Gstroop,
    AOMICTask.WorkingMemory,
]


@register_datagrabber
class DataladAOMICPIOP1(PatternDataladDataGrabber):
    """Concrete implementation for pattern-based data fetching of AOMIC PIOP1.

    Parameters
    ----------
    types : {``DataType.BOLD``, ``DataType.T1w``, \
            ``DataType.VBM_CSF``, ``DataType.VBM_GM``, ``DataType.VBM_WM``, \
            ``DataType.DWI``, ``DataType.FreeSurfer``, ``DataType.Warp``} \
            or list of them, optional
        The data type(s) to grab.
    datadir : pathlib.Path, optional
        That path where the datalad dataset will be cloned.
        If not specified, the datalad dataset will be cloned into a temporary
        directory.
    tasks : {``AOMICTask.RestingState``, ``AOMICTask.Anticipation``, \
            ``AOMICTask.EmoMatching``, ``AOMICTask.Faces``, \
            ``AOMICTask.Gstroop``, ``AOMICTask.WorkingMemory``} or \
            list of them, optional
        AOMIC PIOP1 task sessions.
        By default, all available task sessions are selected.
    space : :enum:`.AOMICSpace`, optional
        AOMIC space (default ``AOMICSpace.MNI152NLin2009cAsym``).

    """

    uri: HttpUrl = HttpUrl("https://github.com/OpenNeuroDatasets/ds002785")
    types: Annotated[
        Union[_types, list[_types]], BeforeValidator(ensure_list)
    ] = [  # noqa: RUF012
        DataType.BOLD,
        DataType.T1w,
        DataType.VBM_CSF,
        DataType.VBM_GM,
        DataType.VBM_WM,
        DataType.DWI,
        DataType.FreeSurfer,
        DataType.Warp,
    ]
    tasks: Annotated[
        Union[_tasks, list[_tasks]], BeforeValidator(ensure_list)
    ] = [  # noqa: RUF012
        AOMICTask.RestingState,
        AOMICTask.Anticipation,
        AOMICTask.EmoMatching,
        AOMICTask.Faces,
        AOMICTask.Gstroop,
        AOMICTask.WorkingMemory,
    ]
    space: AOMICSpace = AOMICSpace.MNI152NLin2009cAsym
    patterns: DataGrabberPatterns = {  # noqa: RUF012
        "BOLD": {
            "pattern": (
                "derivatives/fmriprep/{subject}/func/"
                "{subject}_task-{task}_"
                "{sp_func_desc}"
                "desc-preproc_bold.nii.gz"
            ),
            "mask": {
                "pattern": (
                    "derivatives/fmriprep/{subject}/func/"
                    "{subject}_task-{task}_"
                    "{sp_func_desc}"
                    "desc-brain_mask.nii.gz"
                ),
            },
            "confounds": {
                "pattern": (
                    "derivatives/fmriprep/{subject}/func/"
                    "{subject}_task-{task}_"
                    "desc-confounds_regressors.tsv"
                ),
                "format": "fmriprep",
            },
            "reference": {
                "pattern": (
                    "derivatives/fmriprep/{subject}/func/"
                    "{subject}_task-{task}_"
                    "{sp_func_desc}"
                    "boldref.nii.gz"
                ),
            },
        },
        "T1w": {
            "pattern": (
                "derivatives/fmriprep/{subject}/anat/"
                "{subject}_"
                "{sp_anat_desc}"
                "desc-preproc_T1w.nii.gz"
            ),
            "mask": {
                "pattern": (
                    "derivatives/fmriprep/{subject}/anat/"
                    "{subject}_"
                    "{sp_anat_desc}"
                    "desc-brain_mask.nii.gz"
                ),
            },
        },
        "VBM_CSF": {
            "pattern": (
                "derivatives/fmriprep/{subject}/anat/"
                "{subject}_"
                "{sp_anat_desc}"
                "label-CSF_probseg.nii.gz"
            ),
        },
        "VBM_GM": {
            "pattern": (
                "derivatives/fmriprep/{subject}/anat/"
                "{subject}_"
                "{sp_anat_desc}"
                "label-GM_probseg.nii.gz"
            ),
        },
        "VBM_WM": {
            "pattern": (
                "derivatives/fmriprep/{subject}/anat/"
                "{subject}_"
                "{sp_anat_desc}"
                "label-WM_probseg.nii.gz"
            ),
        },
        "DWI": {
            "pattern": (
                "derivatives/dwipreproc/{subject}/dwi/"
                "{subject}_desc-preproc_dwi.nii.gz"
            ),
        },
        "FreeSurfer": {
            "pattern": "derivatives/freesurfer/[!f]{subject}/mri/T1.mg[z]",
            "aseg": {
                "pattern": (
                    "derivatives/freesurfer/[!f]{subject}/mri/aseg.mg[z]"
                )
            },
            "norm": {
                "pattern": (
                    "derivatives/freesurfer/[!f]{subject}/mri/norm.mg[z]"
                )
            },
            "lh_white": {
                "pattern": (
                    "derivatives/freesurfer/[!f]{subject}/surf/lh.whit[e]"
                )
            },
            "rh_white": {
                "pattern": (
                    "derivatives/freesurfer/[!f]{subject}/surf/rh.whit[e]"
                )
            },
            "lh_pial": {
                "pattern": (
                    "derivatives/freesurfer/[!f]{subject}/surf/lh.pia[l]"
                )
            },
            "rh_pial": {
                "pattern": (
                    "derivatives/freesurfer/[!f]{subject}/surf/rh.pia[l]"
                )
            },
        },
        "Warp": [
            {
                "pattern": (
                    "derivatives/fmriprep/{subject}/anat/"
                    "{subject}_from-MNI152NLin2009cAsym_to-T1w_"
                    "mode-image_xfm.h5"
                ),
                "src": "MNI152NLin2009cAsym",
                "dst": "native",
                "warper": "ants",
            },
            {
                "pattern": (
                    "derivatives/fmriprep/{subject}/anat/"
                    "{subject}_from-T1w_to-MNI152NLin2009cAsym_"
                    "mode-image_xfm.h5"
                ),
                "src": "native",
                "dst": "MNI152NLin2009cAsym",
                "warper": "ants",
            },
        ],
    }
    replacements: list[str] = ["subject", "task"]  # noqa: RUF012
    confounds_format: ConfoundsFormat = ConfoundsFormat.FMRIPrep

    def validate_datagrabber_params(self) -> None:
        """Run extra logical validation for datagrabber."""
        # Descriptor for space in `anat`
        sp_anat_desc = (
            "" if self.space == "native" else "space-MNI152NLin2009cAsym_"
        )
        # Descriptor for space in `func`
        sp_func_desc = (
            "space-T1w_"
            if self.space == "native"
            else "space-MNI152NLin2009cAsym_"
        )
        self.patterns["BOLD"]["pattern"] = self.patterns["BOLD"][
            "pattern"
        ].replace("{sp_func_desc}", sp_func_desc)
        self.patterns["BOLD"]["mask"]["pattern"] = self.patterns["BOLD"][
            "mask"
        ]["pattern"].replace("{sp_func_desc}", sp_func_desc)
        self.patterns["BOLD"]["reference"]["pattern"] = self.patterns["BOLD"][
            "reference"
        ]["pattern"].replace("{sp_func_desc}", sp_func_desc)
        self.patterns["T1w"]["pattern"] = self.patterns["T1w"][
            "pattern"
        ].replace("{sp_anat_desc}", sp_anat_desc)
        self.patterns["T1w"]["mask"]["pattern"] = self.patterns["T1w"]["mask"][
            "pattern"
        ].replace("{sp_anat_desc}", sp_anat_desc)
        for t in ["VBM_CSF", "VBM_GM", "VBM_WM"]:
            self.patterns[t]["pattern"] = self.patterns[t]["pattern"].replace(
                "{sp_anat_desc}", sp_anat_desc
            )
        for t in ["BOLD", "T1w"]:
            self.patterns[t]["space"] = self.space
            self.patterns[t]["mask"]["space"] = self.space
        for t in ["VBM_CSF", "VBM_GM", "VBM_WM"]:
            self.patterns[t]["space"] = self.space
        if self.space == "native":
            self.patterns["BOLD"]["prewarp_space"] = "MNI152NLin2009cAsym"
        else:
            self.patterns["BOLD"]["prewarp_space"] = "native"
        super().validate_datagrabber_params()

    def get_item(self, subject: str, task: str) -> dict:
        """Get the specified item from the dataset.

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

        return super().get_item(subject=subject, task=new_task)

    def get_elements(self) -> list:
        """Implement fetching list of subjects in the dataset.

        Returns
        -------
        list of str
            The list of subjects in the dataset.

        """
        subjects = [f"sub-{x:04d}" for x in range(1, 217)]
        elems = []
        for subject, task in product(subjects, self.tasks):
            elems.append((subject, task))

        return elems
