"""Provide concrete implementation for pattern-based HCP1200 DataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from itertools import product
from pathlib import Path
from typing import Union

from ...api.decorators import register_datagrabber
from ...utils import raise_error
from ..pattern import PatternDataGrabber


__all__ = ["HCP1200"]


@register_datagrabber
class HCP1200(PatternDataGrabber):
    """Concrete implementation for pattern-based data fetching of HCP1200.

    Parameters
    ----------
    datadir : str or Path, optional
        The directory where the data is / will be stored.
    tasks : {"REST1", "REST2", "SOCIAL", "WM", "RELATIONAL", "EMOTION", \
            "LANGUAGE", "GAMBLING", "MOTOR"} or list of the options or None \
            , optional
        HCP task sessions. If None, all available task sessions are selected
        (default None).
    phase_encodings : {"LR", "RL"} or list of the options or None, optional
        HCP phase encoding directions. If None, both will be used
        (default None).
    ica_fix : bool, optional
        Whether to retrieve data that was processed with ICA+FIX.
        Only "REST1" and "REST2" tasks are available with ICA+FIX (default
        False).

    Raises
    ------
    ValueError
        If invalid value is passed for ``tasks`` or ``phase_encodings``.

    """

    def __init__(
        self,
        datadir: Union[str, Path],
        tasks: Union[str, list[str], None] = None,
        phase_encodings: Union[str, list[str], None] = None,
        ica_fix: bool = False,
    ) -> None:
        # All tasks
        all_tasks = [
            "REST1",
            "REST2",
            "SOCIAL",
            "WM",
            "RELATIONAL",
            "EMOTION",
            "LANGUAGE",
            "GAMBLING",
            "MOTOR",
        ]
        # Set default tasks
        if tasks is None:
            self.tasks: list[str] = all_tasks
        # Convert single task into list
        else:
            if not isinstance(tasks, list):
                tasks = [tasks]
            # Check for invalid task(s)
            for task in tasks:
                if task not in all_tasks:
                    raise_error(
                        f"'{task}' is not a valid HCP-YA fMRI task input. "
                        f"Valid task values can be any or all of {all_tasks}."
                    )
            self.tasks: list[str] = tasks

        # All phase encodings
        all_phase_encodings = ["LR", "RL"]
        # Set phase encodings
        if phase_encodings is None:
            phase_encodings = all_phase_encodings
        # Convert single phase encoding into list
        if isinstance(phase_encodings, str):
            phase_encodings = [phase_encodings]
        # Check for invalid phase encoding(s)
        for pe in phase_encodings:
            if pe not in all_phase_encodings:
                raise_error(
                    f"'{pe}' is not a valid HCP-YA phase encoding. "
                    "Valid phase encoding can be any or all of "
                    f"{all_phase_encodings}."
                )
        self.phase_encodings = phase_encodings

        if ica_fix:
            if not all(task in ["REST1", "REST2"] for task in self.tasks):
                raise_error(
                    "ICA+FIX is only available for 'REST1' and 'REST2' tasks."
                )
        suffix = "_hp2000_clean" if ica_fix else ""

        # The types of data
        types = ["BOLD", "T1w", "Warp"]
        # The patterns
        patterns = {
            "BOLD": {
                "pattern": (
                    "{subject}/MNINonLinear/Results/"
                    "{task}_{phase_encoding}/"
                    "{task}_{phase_encoding}"
                    f"{suffix}.nii.gz"
                ),
                "space": "MNI152NLin6Asym",
            },
            "T1w": {
                "pattern": "{subject}/T1w/T1w_acpc_dc_restore.nii.gz",
                "space": "native",
            },
            "Warp": [
                {
                    "pattern": (
                        "{subject}/MNINonLinear/xfms/standard2acpc_dc.nii.gz"
                    ),
                    "src": "MNI152NLin6Asym",
                    "dst": "native",
                    "warper": "fsl",
                },
                {
                    "pattern": (
                        "{subject}/MNINonLinear/xfms/acpc_dc2standard.nii.gz"
                    ),
                    "src": "native",
                    "dst": "MNI152NLin6Asym",
                    "warper": "fsl",
                },
            ],
        }
        # The replacements
        replacements = ["subject", "task", "phase_encoding"]
        super().__init__(
            types=types,
            datadir=datadir,
            patterns=patterns,
            replacements=replacements,
        )

    def get_item(self, subject: str, task: str, phase_encoding: str) -> dict:
        """Implement single element indexing in the database.

        Parameters
        ----------
        subject : str
            The subject ID.
        task : {"REST1", "REST2", "SOCIAL", "WM", "RELATIONAL", "EMOTION", \
               "LANGUAGE", "GAMBLING", "MOTOR"}
            The task.
        phase_encoding : {"LR", "RL"}
            The phase encoding.

        Returns
        -------
        dict
            Dictionary of dictionaries for each type of data required for the
            specified element.

        """
        # Resting task
        if "REST" in task:
            new_task = f"rfMRI_{task}"
        else:
            new_task = f"tfMRI_{task}"

        return super().get_item(
            subject=subject, task=new_task, phase_encoding=phase_encoding
        )

    def get_elements(self) -> list:
        """Implement fetching list of elements in the dataset.

        Returns
        -------
        list
            The list of elements that can be grabbed in the dataset.

        """
        subjects = [
            x.name
            for x in self.datadir.iterdir()
            if x.is_dir() and not x.name.startswith(".")
        ]
        elems = []
        for subject, task, phase_encoding in product(
            subjects, self.tasks, self.phase_encodings
        ):
            elems.append((subject, task, phase_encoding))

        return elems
