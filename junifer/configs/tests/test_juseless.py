import socket
import pytest

from junifer.configs.juseless import JuselessDataladUKBVBM
from junifer.utils.logging import configure_logging

if socket.gethostname() != 'juseless':
    pytest.skip('This tests are only for juseless', allow_module_level=True)

configure_logging(level='DEBUG')


def test_juselessdataladukbvbm_datagrabber():
    with JuselessDataladUKBVBM() as dg:
        out = dg[('sub-2670511', 'ses-2')]
        assert 'VBM_GM' in out
        assert out['VBM_GM'].name == 'm0wp1sub-2670511_ses-2_T1w.nii.gz'
        assert out['VBM_GM'].exists()
