"""Provide concrete implementations for HCP data access."""

from itertools import product
from pathlib import Path
from typing import Dict, List, Tuple, Union

from junifer.datagrabber.datalad_base import DataladDataGrabber

from ..api.decorators import register_datagrabber
from ..utils import raise_error
from .pattern import PatternDataGrabber


@register_datagrabber
class AOMIC1000(PatternDataGrabber):
    """Concrete implementation for pattern-based data fetching of AOMIC1000.

    Parameters
    ----------
    datadir : str or Path, optional
        The directory where the datalad dataset will be cloned. If None,
        the datalad dataset will be cloned into a temporary directory
        (default None).
    tasks : {"moviewatching"} AOMIC 1000 tasks.
        If None, moviewatching is selected.
        (default None).
    **kwargs
        Keyword arguments passed to superclass.

    """

    def __init__(
        self,
        datadir: Union[str, Path, None] = None,
        tasks: Union[str, List[str], None] = None,
        **kwargs,
    ) -> None:
        """Initialize the class."""
        # All tasks
        all_tasks = [
            "moviewatching",
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
                        f"'{task}' is not a valid AOMIC fMRI task input. "
                        f"Valid task values can be {all_tasks}."
                    )
            self.tasks: List[str] = tasks

        # The types of data
        types = ["BOLD"]
        # The patterns
        patterns = {
            "BOLD": (
                "derivatives/fmriprep/sub-{subject}/func/"
                "sub-{subject}_task-{tasks}_"
                "space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz"
            )
        }
        # The replacements
        replacements = ["subject", "tasks"]
        super().__init__(
            types=types,
            datadir=datadir,
            patterns=patterns,
            replacements=replacements,
        )

    def __getitem__(self, element: Tuple[str, str, str]) -> Dict[str, Path]:
        """Index one element in the dataset.

        Parameters
        ----------
        element : triple of str
            The element to be indexed. First element in the tuple is the
            subject, second element is the task.

        Returns
        -------
        out : dict
            Dictionary of paths for each type of data required for the
            specified element.

        """
        sub, task = element

        out = super().__getitem__((sub, task))
        out["meta"]["element"] = {
            "subject": sub,
            "task": task,
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
        for subject, task in product(
            subjects, self.tasks
        ):
            elems.append((subject, task))

        return elems


@register_datagrabber
class DataladAOMIC1000(DataladDataGrabber, AOMIC1000):
    """Concrete implementation for datalad-based data fetching of AOMIC1000.

    Parameters
    ----------
    datadir : str or Path, optional
        The directory where the datalad dataset will be cloned. If None,
        the datalad dataset will be cloned into a temporary directory
        (default None).
    tasks : {"moviewatching"} AOMIC 1000 tasks.
        If None, moviewatching is selected.
        (default None).
    **kwargs
        Keyword arguments passed to superclass.

    """

    def __init__(
        self,
        datadir: Union[str, Path, None] = None,
        tasks: Union[str, List[str], None] = None,
        **kwargs,
    ) -> None:
        """Initialize the class."""
        uri = (
            "https://github.com/OpenNeuroDatasets/ds003097.git"
        )
        rootdir = "derivatives"
        super().__init__(
            datadir=datadir,
            tasks=tasks,
            uri=uri,
            rootdir=rootdir,
        )
