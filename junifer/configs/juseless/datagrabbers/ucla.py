"""Provide concrete implementation for UCLA DataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import List, Union

from ....api.decorators import register_datagrabber
from ....datagrabber import PatternDataGrabber
from ....utils import raise_error


@register_datagrabber
class JuselessUCLA(PatternDataGrabber):
    """Concrete implementation for Juseless UCLA data fetching.

    Implements a DataGrabber to access the UCLA data in Juseless.

    Parameters
    ----------
    datadir : str or Path, optional
        The directory where the dataset is stored.
        (default "/data/project/psychosis_thalamus/data/fmriprep").
    types: {"BOLD", "BOLD_confounds", "T1w", "probseg_CSF", "probseg_GM", \
           "probseg_WM"} or a list of the options, optional
        UCLA data types. If None, all available data types are selected.
        (default None).
    tasks : {"rest", "bart", "bht", "pamenc", "pamret", \
            "scap", "taskswitch", "stopsignal"} or \
            list of the options or None, optional
        UCLA task sessions. If None, all available task sessions are
        selected (default None).

    """

    def __init__(
        self,
        datadir: Union[
            str, Path
        ] = "/data/project/psychosis_thalamus/data/fmriprep",
        types: Union[str, List[str], None] = None,
        tasks: Union[str, List[str], None] = None,
    ) -> None:
        # Declare all tasks
        all_tasks = [
            "rest",
            "bart",
            "bht",
            "pamenc",
            "pamret",
            "scap",
            "taskswitch",
            "stopsignal",
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
                        f"{t} is not a valid task in the UCLA dataset!"
                    )
        self.tasks = tasks
        # The patterns
        patterns = {
            "BOLD": (
                "sub-{subject}/func/sub-{subject}_task-{task}_bold_space-"
                "MNI152NLin2009cAsym_preproc.nii.gz"
            ),
            "BOLD_confounds": (
                "sub-{subject}/func/sub-{subject}_"
                "task-{task}_bold_confounds.tsv"
            ),
            "T1w": (
                "sub-{subject}/anat/sub-{subject}_"
                "T1w_space-MNI152NLin2009cAsym_preproc.nii.gz"
            ),
            "probseg_CSF": (
                "sub-{subject}/anat/sub-{subject}_T1w_space-"
                "MNI152NLin2009cAsym_class-CSF_probtissue.nii.gz"
            ),
            "probseg_GM": (
                "sub-{subject}/anat/sub-{subject}_T1w_space-"
                "MNI152NLin2009cAsym_class-GM_probtissue.nii.gz"
            ),
            "probseg_WM": (
                "sub-{subject}/anat/sub-{subject}_T1w_space"
                "-MNI152NLin2009cAsym_class-WM_probtissue.nii.gz"
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
        # the commented out uri leads to new open neuro dataset which does
        # NOT have preprocessed data
        # uri = "https://github.com/OpenNeuroDatasets/ds000030.git"
        super().__init__(
            types=types,
            datadir=datadir,
            patterns=patterns,
            replacements=replacements,
            confounds_format="fmriprep",
        )

    def get_elements(self) -> List:
        """Implement fetching list of elements in the dataset.

        Returns
        -------
        elements : list
            The list of elements that can be grabbed in the dataset after
            imposing constraints based on specified tasks.

        """
        return [x for x in super().get_elements() if x[1] in self.tasks]
