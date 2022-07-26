"""Provide testing datagrabbers."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import tempfile
from nilearn import datasets

from ..datagrabber.base import BaseDataGrabber


class OasisVBMTestingDatagrabber(BaseDataGrabber):
    """DataGrabber for Oasis VBM testing data."""

    def __init__(self):
        """Initialize class."""
        datadir = tempfile.mkdtemp()
        types = ['VBM_GM']
        super().__init__(types=types, datadir=datadir)

    def get_elements(self):
        """Get elements."""
        return [f'sub-{x:02d}' for x in list(range(1, 11))]

    def __getitem__(self, element):
        """Get item implementation."""
        out = super().__getitem__(element)
        i_sub = int(element.split('-')[1]) - 1
        out['VBM_GM'] = {'path': self._dataset.gray_matter_maps[i_sub]}
        # Set the element accordingly
        out['meta']['element'] = {'subject': element}
        return out

    def __enter__(self):
        """Context enter implementation."""
        self._dataset = datasets.fetch_oasis_vbm(n_subjects=10)
        return self
