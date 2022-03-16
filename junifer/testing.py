# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
import tempfile
from nilearn import datasets

from .datagrabber.base import BaseDataGrabber
from .api.registry import register


def register_testing():
    """Register testing datagrabber"""
    register(
        'datagrabber', 'OasisVBMTestingDatagrabber',
        OasisVBMTestingDatagrabber)


class OasisVBMTestingDatagrabber(BaseDataGrabber):
    """
    DataGrabber for Oasis VBM testing data.
    """
    def __init__(self):
        datadir = tempfile.mkdtemp()
        types = ['VBM_GM']
        super().__init__(types=types, datadir=datadir)

    def get_elements(self):
        return list(range(1, 11))

    def __getitem__(self, element):
        out = {}
        out['VBM_GM'] = self._dataset.gray_matter_maps[element - 1]
        out['meta'] = {'element': {'subject': element}}
        return out

    def __enter__(self):
        self._dataset = datasets.fetch_oasis_vbm(n_subjects=10)
        return self
