"""Provide concrete implementations for HCP data access."""

from itertools import product
from pathlib import Path
from typing import Dict, List, Tuple, Union

from junifer.datagrabber.datalad_base import DataladDataGrabber

from ..api.decorators import register_datagrabber
from ..utils import raise_error
from .pattern import PatternDataGrabber


@register_datagrabber
class HCP1200(PatternDataGrabber):
    """Concrete implementation for pattern-based data fetching of HCP1200.

    Parameters
    ----------
    datadir : str or Path, optional
        The directory where the datalad dataset will be cloned. If None,
        the datalad dataset will be cloned into a temporary directory
        (default None).
    tasks : {"REST1", "REST2", "SOCIAL", "WM", "RELATIONAL", "EMOTION",
        "LANGUAGE", "GAMBLING", "MOTOR"} or list of the options, optional
        HCP task sessions. If None, all available task sessions are selected
        (default None).
    phase_encodings : {"LR", "RL"} or list of the options, optional
        HCP phase encoding directions. If None, both will be used
        (default None).
    **kwargs
        Keyword arguments passed to superclass.

    """

    def __init__(
        self,
        datadir: Union[str, Path, None] = None,
        tasks: Union[str, List[str], None] = None,
        phase_encodings: Union[str, List[str], None] = None,
        **kwargs,
    ) -> None:
        """Initialize the class."""
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
            self.tasks: List[str] = all_tasks
        # Convert single task into list
        else:
            if not isinstance(tasks, List):
                tasks = [tasks]
            # Check for invalid task(s)
            for task in tasks:
                if task not in all_tasks:
                    raise_error(
                        f"'{task}' is not a valid HCP-YA fMRI task input. "
                        f"Valid task values can be any or all of {all_tasks}."
                    )
            self.tasks: List[str] = tasks
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

        # The types of data
        types = ["BOLD"]
        # The patterns
        patterns = {
            "BOLD": (
                "{subject}/MNINonLinear/Results/"
                "{task}_{phase_encoding}/"
                "{task}_{phase_encoding}_hp2000_clean.nii.gz"
            )
        }
        # The replacements
        replacements = ["subject", "task", "phase_encoding"]
        super().__init__(
            types=types,
            datadir=datadir,
            patterns=patterns,
            replacements=replacements,
        )
        self.phase_encodings = phase_encodings

    def __getitem__(self, element: Tuple[str, str, str]) -> Dict[str, Path]:
        """Index one element in the dataset.

        Parameters
        ----------
        element : triple of str
            The element to be indexed. First element in the tuple is the
            subject, second element is the task, third element is the
            phase encoding direction.

        Returns
        -------
        out : dict
            Dictionary of paths for each type of data required for the
            specified element.

        """
        sub, task, phase_encoding = element

        # Resting task
        if "REST" in task:
            new_task = f"rfMRI_{task}"
        else:
            new_task = f"tfMRI_{task}"

        out = super().__getitem__((sub, new_task, phase_encoding))
        out["meta"]["element"] = {
            "subject": sub,
            "task": task,
            "phase_encoding": phase_encoding,
        }
        return out

    def get_elements(self) -> List:
        """Implement fetching list of subjects in the dataset.

        Returns
        -------
        elements : list of str
            The list of subjects in the dataset.

        """
        subjects = [x.name for x in self.datadir.iterdir() if x.is_dir()]
        elems = []
        for subject, task, phase_encoding in product(
            subjects, self.tasks, self.phase_encodings
        ):
            elems.append((subject, task, phase_encoding))

        return elems


@register_datagrabber
class DataladHCP1200(DataladDataGrabber, HCP1200):
    """Concrete implementation for datalad-based data fetching of HCP1200.

    Parameters
    ----------
    datadir : str or Path, optional
        The directory where the datalad dataset will be cloned. If None,
        the datalad dataset will be cloned into a temporary directory
        (default None).
    tasks : {"REST1", "REST2", "SOCIAL", "WM", "RELATIONAL", "EMOTION",
        "LANGUAGE", "GAMBLING", "MOTOR"} or list of the options, optional
        HCP task sessions. If None, all available task sessions are selected
        (default None).
    phase_encodings : {"LR", "RL"} or list of the options, optional
        HCP phase encoding directions. If None, both will be used
        (default None).
    **kwargs
        Keyword arguments passed to superclass.

    """

    def __init__(
        self,
        datadir: Union[str, Path, None] = None,
        tasks: Union[str, List[str], None] = None,
        phase_encodings: Union[str, List[str], None] = None,
        **kwargs,
    ) -> None:
        """Initialize the class."""
        uri = (
            "https://github.com/datalad-datasets/"
            "human-connectome-project-openaccess.git"
        )
        rootdir = "HCP1200"
        super().__init__(
            datadir=datadir,
            tasks=tasks,
            phase_encodings=phase_encodings,
            uri=uri,
            rootdir=rootdir,
        )

    @property
    def skip_file_check(self) -> bool:
        """Skip file check existence."""
        return True
