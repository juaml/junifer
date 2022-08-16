"""Provide tests for base."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

import pytest

from junifer.datagrabber.base import BaseDataGrabber


def test_BaseDataGrabber_abstractness() -> None:
    """Test BaseDataGrabber is abstract base class."""
    with pytest.raises(TypeError, match=r"abstract"):
        BaseDataGrabber(datadir="/tmp", types=["func"])


def test_BaseDataGrabber() -> None:
    """Test BaseDataGrabber."""
    # Create concrete class.
    class MyDataGrabber(BaseDataGrabber):
        def __getitem__(self, element):
            return super().__getitem__(element)

        def get_elements(self):
            return super().get_elements()

    dg = MyDataGrabber(datadir="/tmp", types=["func"])
    elem = dg["elem"]
    assert "meta" in elem
    assert "datagrabber" in elem["meta"]
    assert "class" in elem["meta"]["datagrabber"]
    assert MyDataGrabber.__name__ in elem["meta"]["datagrabber"]["class"]

    with pytest.raises(NotImplementedError):
        dg.get_elements()

    with dg:
        assert dg.datadir == Path("/tmp")
        assert dg.types == ["func"]
