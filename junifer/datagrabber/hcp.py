import os
from itertools import product
from ..datagrabber import DataladDataGrabber
from ..api.decorators import register_datagrabber


@register_datagrabber
class HCP1200(DataladDataGrabber):
    """ Human Connectome Project Datalad DataGrabber class

    Implements a DataGrabber to access the Human Connectome Project
    
    """
    def __init__(self, datadir=None):
        """Initialize a HCP object.

        Parameters
        ----------
        datadir : str or Path
            That directory where the datalad dataset will be cloned. If None,
            (default), the datalad dataset will be cloned into a temporary
            directory.

        """
        uri = (
            'https://github.com/datalad-datasets/'
            'human-connectome-project-openaccess.git'
        )
        rootdir = 'HCP1200'
        types = ['BOLD', 'T1w']
        super().__init__(
            types=types, datadir=datadir, uri=uri, rootdir=rootdir
        )

    def get_elements(self, subjects=None, tasks=None, phase_encodings=None):
        """Get the list of subjects in the dataset.

        Returns
        -------
        elements : list[str]
            The list of subjects in the dataset.
        """
        elems = []

        if isinstance(subjects, str):
            subjects = [subjects]
        if isinstance(tasks, str):
            tasks = [tasks]
        if isinstance(phase_encodings, str):
            phase_encodings = [phase_encodings]

        if subjects is None:
            subjects = os.listdir(self.datadir)
        if tasks is None:
            tasks = [
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
        if phase_encodings is None:
            phase_encodings = ["LR", "RL"]

        for subject, task, phase_encoding in product(
            subjects, tasks, phase_encodings
        ):
            elems.append((subject, task, phase_encoding))
        
        return elems

    def __getitem__(self, element):
        """Index one element in the dataset.

        Parameters
        ----------
        element : tuple[str, str]
            The element to be indexed. First element in the tuple is the
            subject, second element is the task, third element is the 
            phase encoding direction.

        Returns
        -------
        out : dict[str -> Path]
            Dictionary of paths for each type of data required for the
            specified element.
        """
        sub, task, phase_encoding = element
        out = {}

        if "REST" in task:
            task_name = f"rfMRI_{task}"
        else:
            task_name = f"tfMRI_{task}"
        
        out["BOLD"] = dict(
            path=self.datadir / sub / "MNINonLinear" / "Results" / 
            f"{task_name}_{phase_encoding}" / 
            f"{task_name}_{phase_encoding}_hp2000_clean.nii.gz"
        )

        self._dataset_get(out)

        out['meta']['element'] = dict(
            subject=sub, task=task, phase_encoding=phase_encoding
        )

        return out