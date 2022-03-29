from itertools import product

from junifer.datagrabber.base import DataladDataGrabber

from ..datagrabber import PatternDataGrabber
from ..api.decorators import register_datagrabber


@register_datagrabber
class HCP1200(PatternDataGrabber):

    def __init__(
        self, datadir=None, tasks=None, phase_encodings=None
    ):
        """Initialize a HCP object.

        Parameters
        ----------
        datadir : str or Path
            That directory where the datalad dataset will be cloned. If None,
            (default), the datalad dataset will be cloned into a temporary
            directory.
        tasks : str or list of strings
            HCP task sessions. If 'None' (default), all available task
            sessions are selected. Can be 'REST1', 'REST2', 'SOCIAL', 'WM',
            'RELATIONAL', 'EMOTION', 'LANGUAGE', 'GAMBLING', 'MOTOR', or a
            list consisting of these names.
        phase_encoding : str or list of strings
            HCP phase encoding directions. Can be 'LR' or 'RL'. If 'None'
            (default) both will be used.

        """

        types = ['BOLD']
        # TODO: Validate tasks
        # TODO: Validate phase_encodings

        replacements = ['subject', 'task', 'phase_encoding']
        patterns = {
            'BOLD': ('{subject}/MNINonLinear/Results/'
                     '{task}_{phase_encoding}/'
                     '{task}_{phase_encoding}_hp2000_clean.nii.gz')
        }
        super().__init__(
            types=types, datadir=datadir, patterns=patterns,
            replacements=replacements
        )

        self.tasks = tasks
        self.phase_encodings = phase_encodings

        if isinstance(self.tasks, str):
            self.tasks = [self.tasks]
        if isinstance(self.phase_encodings, str):
            self.phase_encodings = [self.phase_encodings]

        if self.tasks is None:
            self.tasks = [
                'REST1',
                'REST2',
                'SOCIAL',
                'WM',
                'RELATIONAL',
                'EMOTION',
                'LANGUAGE',
                'GAMBLING',
                'MOTOR',
            ]

        if self.phase_encodings is None:
            self.phase_encodings = ['LR', 'RL']

    def get_elements(self):
        """Get the list of subjects in the dataset.

        Returns
        -------
        elements : list[str]
            The list of subjects in the dataset.
        """

        subjects = [x.name for x in self.datadir.iterdir() if x.is_dir()]
        elems = []
        for subject, task, phase_encoding in product(
            subjects, self.tasks, self.phase_encodings
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

        if "REST" in task:
            new_task = f'rfMRI_{task}'
        else:
            new_task = f'tfMRI_{task}'

        out = super().__getitem__((sub, new_task, phase_encoding))
        out['meta']['element'] = dict(
            subject=sub, task=task, phase_encoding=phase_encoding
        )

        return out


@register_datagrabber
class DataladHCP1200(DataladDataGrabber, HCP1200,):
    def __init__(self, datadir=None, tasks=None, phase_encodings=None):
        uri = (
            'https://github.com/datalad-datasets/'
            'human-connectome-project-openaccess.git'
        )
        rootdir = 'HCP1200'
        super().__init__(datadir=datadir, tasks=tasks,
                         phase_encodings=phase_encodings,
                         uri=uri, rootdir=rootdir)  # type: ignore
