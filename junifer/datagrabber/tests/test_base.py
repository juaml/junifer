# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL
import pytest
from pathlib import Path
from junifer.datagrabber.base import BIDSDataGrabber


def test_bidsdatagrabber():
    """Test BIDSDataGrabber"""
    with pytest.raises(TypeError, match=r"types must be a list"):
        BIDSDataGrabber(datadir='/tmp', types='wrong',
                        patterns=dict(wrong='pattern'))

    with pytest.raises(TypeError, match=r"must be a list of strings"):
        BIDSDataGrabber(datadir='/tmp', types=[1, 2, 3],
                        patterns={'1': 'pattern', '2': 'pattern',
                                  '3': 'pattern'})

    datagrabber = BIDSDataGrabber(
        datadir='/tmp/data', types=['func', 'anat'],
        patterns=dict(func='pattern1', anat='pattern2'))
    assert datagrabber.datadir == Path('/tmp/data')
    assert datagrabber.types == ['func', 'anat']
