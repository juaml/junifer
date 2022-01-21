import pytest
from pathlib import Path
from junifer.datagrabber.base import BaseDataGrabber


def test_basedatagrabber():
    """Test BaseDataGrabber"""
    with pytest.raises(TypeError, match=r"types must be a list"):
        BaseDataGrabber('/tmp', 'wrong')

    with pytest.raises(TypeError, match=r"must be a list of strings"):
        BaseDataGrabber('/tmp', [1, 2, 3])

    datagrabber = BaseDataGrabber('/tmp/data', ['func', 'anat'])
    assert datagrabber.datadir == Path('/tmp/data')
    assert datagrabber.types == ['func', 'anat']

    with pytest.raises(NotImplementedError, match=r"get_elements not"):
        datagrabber.get_elements()

    with pytest.raises(NotImplementedError, match=r"__getitem__ not"):
        datagrabber['sub-42']
