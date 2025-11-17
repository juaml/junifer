"""Provide concrete implementation for UCLA DataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL

from enum import Enum
from pathlib import Path
from typing import Literal

from ....api.decorators import register_datagrabber
from ....datagrabber import ConfoundsFormat, DataType, PatternDataGrabber
from ....typing import DataGrabberPatterns


__all__ = ["JuselessUCLA"]


class UCLATask(str, Enum):
    """Accepted UCLA tasks."""

    REST = "rest"
    BART = "bart"
    BHT = "bht"
    PAMENC = "pamenc"
    PAMRET = "pamret"
    SCAP = "scap"
    TASKSWITCH = "taskswitch"
    STOPSIGNAL = "stopsignal"


@register_datagrabber
class JuselessUCLA(PatternDataGrabber):
    """Concrete implementation for Juseless UCLA data fetching.

    Implements a DataGrabber to access the UCLA data in Juseless.

    Parameters
    ----------
    datadir : Path, optional
        The directory where the dataset is stored.
        (default "/data/project/psychosis_thalamus/data/fmriprep").
    types: list of {``DataType.BOLD``, ``DataType.T1w``, \
           ``DataType.VBM_CSF``, ``DataType.VBM_GM``, ``DataType.VBM_WM``}, \
           optional
        The data type(s) to grab.
    tasks : list of ``UCLATask``, optional
        UCLA task sessions.
        By default, all available task are selected.

    """

    # the commented out uri leads to new open neuro dataset which does
    # NOT have preprocessed data
    # uri = "https://github.com/OpenNeuroDatasets/ds000030.git"
    datadir: Path = Path("/data/project/psychosis_thalamus/data/fmriprep")
    types: list[
        Literal[
            DataType.BOLD,
            DataType.T1w,
            DataType.VBM_CSF,
            DataType.VBM_GM,
            DataType.VBM_WM,
        ]
    ] = [  # noqa: RUF012
        DataType.BOLD,
        DataType.T1w,
        DataType.VBM_CSF,
        DataType.VBM_GM,
        DataType.VBM_WM,
    ]
    tasks: list[UCLATask] = [  # noqa: RUF012
        UCLATask.REST,
        UCLATask.BART,
        UCLATask.BHT,
        UCLATask.PAMENC,
        UCLATask.PAMRET,
        UCLATask.SCAP,
        UCLATask.TASKSWITCH,
        UCLATask.STOPSIGNAL,
    ]
    patterns: DataGrabberPatterns = {  # noqa: RUF012
        "BOLD": {
            "pattern": (
                "{subject}/func/{subject}_task-{task}_bold_space-"
                "MNI152NLin2009cAsym_preproc.nii.gz"
            ),
            "space": "MNI152NLin2009cAsym",
            "confounds": {
                "pattern": (
                    "{subject}/func/{subject}_task-{task}_bold_confounds.tsv"
                ),
                "space": "fmriprep",
            },
        },
        "T1w": {
            "pattern": (
                "{subject}/anat/{subject}_"
                "T1w_space-MNI152NLin2009cAsym_preproc.nii.gz"
            ),
            "space": "MNI152NLin2009cAsym",
        },
        "VBM_CSF": {
            "pattern": (
                "{subject}/anat/{subject}_T1w_space-"
                "MNI152NLin2009cAsym_class-CSF_probtissue.nii.gz"
            ),
            "space": "MNI152NLin2009cAsym",
        },
        "VBM_GM": {
            "pattern": (
                "{subject}/anat/{subject}_T1w_space-"
                "MNI152NLin2009cAsym_class-GM_probtissue.nii.gz"
            ),
            "space": "MNI152NLin2009cAsym",
        },
        "VBM_WM": {
            "pattern": (
                "{subject}/anat/{subject}_T1w_space"
                "-MNI152NLin2009cAsym_class-WM_probtissue.nii.gz"
            ),
            "space": "MNI152NLin2009cAsym",
        },
    }
    replacements: list[str] = ["subject", "task"]  # noqa: RUF012
    confounds_format: ConfoundsFormat = ConfoundsFormat.FMRIPrep

    def get_elements(self) -> list:
        """Implement fetching list of elements in the dataset.

        Returns
        -------
        elements : list
            The list of elements that can be grabbed in the dataset after
            imposing constraints based on specified tasks.

        """
        return [x for x in super().get_elements() if x[1] in self.tasks]
