"""Provide a concrete implementation for UCLA dataset."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import List, Union
from junifer.datagrabber import PatternDataladDataGrabber

from ...api.decorators import register_datagrabber
from ...utils import raise_error

@register_datagrabber
class DataladUCLA(PatternDataladDataGrabber):
    """Concrete implementation for pattern-based data fetching of UCLA data.
    
    Parameters
    ----------
    datadir : str or Path, optional
        The directory where the datalad dataset will be cloned. If None,
        the datalad dataset will be cloned into a temporary directory
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
        """Initialise the class."""
        types = []

        if isinstance(tasks, str):
            tasks = [tasks]

        all_tasks = [
            "rest",
            "bart",
            "bht",
            "pamenc",
            "pamret",
            "scap",
            "taskswitch",
            "stopsignal"
        ]

        if tasks is None:
            tasks = all_tasks
        else:
            for t in tasks:
                if t not in all_tasks:
                    raise_error(
                        f"{t} is not a valid task in the UCLA"
                        " dataset!"
                    )

        self.tasks = tasks


        patterns = {

        }


        # the commented out uri leads to new open neuro dataset which does 
        # NOT have preprocessed data
        # uri = "https://github.com/OpenNeuroDatasets/ds000030.git"
        # The below uri leads to legacy openfmri dataset which does have the
        # preprocessed fmriprep derivatives:
        uri = "///openfmri/ds000030/"
        
        replacements = []
        super().__init__(
            types=types,
            datadir=datadir,
            uri=uri,
            patterns=patterns,
            replacements=replacements
        )