import socket
import pytest
import os

from junifer.configs.juseless import JuselessDataladUKBVBM
from junifer.utils.logging import configure_logging
from junifer.datagrabber.hcp import DataladHCP1200

if socket.gethostname() != 'juseless':
    pytest.skip('This tests are only for juseless', allow_module_level=True)

configure_logging(level='DEBUG')


def test_juselessdataladukbvbm_datagrabber():
    with JuselessDataladUKBVBM() as dg:
        out = dg[('2670511', '2')]
        assert 'VBM_GM' in out
        assert out['VBM_GM'].name == 'm0wp1sub-2670511_ses-2_T1w.nii.gz'
        assert out['VBM_GM'].exists()


def test_juselessdataladhcp_datagrabber():
    with DataladHCP1200() as dg:
        all_elements = dg.get_elements()
        test_element = all_elements[0]

        out = dg[test_element]

        assert out['BOLD'].exists()
        assert os.path.isfile(out['BOLD']['path'])
