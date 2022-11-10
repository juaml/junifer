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
        BaseDataGrabber(datadir="/tmp", types=["func"])  # type: ignore


def test_BaseDataGrabber() -> None:
    """Test BaseDataGrabber."""
    # Create concrete class.
    class MyDataGrabber(BaseDataGrabber):
        def get_item(self, subject):
            return {}

        def get_elements(self):
            return super().get_elements()

        def get_element_keys(self):
            return ["subject"]

    dg = MyDataGrabber(datadir="/tmp", types=["func"])
    elem = dg["elem"]
    assert "meta" in elem
    assert "datagrabber" in elem["meta"]
    assert "class" in elem["meta"]["datagrabber"]
    assert MyDataGrabber.__name__ in elem["meta"]["datagrabber"]["class"]
    assert "element" in elem["meta"]
    assert "subject" in elem["meta"]["element"]
    assert "elem" in elem["meta"]["element"]["subject"]

    with pytest.raises(NotImplementedError):
        dg.get_elements()

    with dg:
        assert dg.datadir == Path("/tmp")
        assert dg.types == ["func"]

    class MyDataGrabber2(BaseDataGrabber):
        def get_item(self, subject):
            return super().get_item(subject=subject)

        def get_elements(self):
            return super().get_elements()

        def get_element_keys(self):
            return super().get_element_keys()
    dg = MyDataGrabber2(datadir="/tmp", types=["func"])
    with pytest.raises(NotImplementedError):
        dg.get_element_keys()

    with pytest.raises(NotImplementedError):
        dg.get_item(subject=1)  # type: ignore
