"""Provide tests for BaseDataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

import pytest

from junifer.datagrabber import BaseDataGrabber


def test_BaseDataGrabber() -> None:
    """Test BaseDataGrabber."""

    # Create concrete class.
    class MyDataGrabber(BaseDataGrabber):
        def get_item(self, subject):
            return {"BOLD": {}}

        def get_elements(self):
            return super().get_elements()

        def get_element_keys(self):
            return ["subject"]

    dg = MyDataGrabber(datadir="/tmp", types=["BOLD"])
    elem = dg["sub01"]
    assert "BOLD" in elem
    assert "meta" in elem["BOLD"]
    meta = elem["BOLD"]["meta"]
    assert "datagrabber" in meta
    assert "class" in meta["datagrabber"]
    assert MyDataGrabber.__name__ in meta["datagrabber"]["class"]
    assert "element" in meta
    assert "subject" in meta["element"]
    assert "sub01" in meta["element"]["subject"]

    with pytest.raises(NotImplementedError):
        dg.get_elements()

    with dg:
        assert dg.datadir == Path("/tmp")
        assert dg.types == ["BOLD"]

    class MyDataGrabber2(BaseDataGrabber):
        def get_item(self, subject):
            return super().get_item(subject=subject)

        def get_elements(self):
            return super().get_elements()

        def get_element_keys(self):
            return super().get_element_keys()

    dg = MyDataGrabber2(datadir="/tmp", types=["BOLD"])
    with pytest.raises(NotImplementedError):
        dg.get_element_keys()

    with pytest.raises(NotImplementedError):
        dg.get_item(subject=1)  # type: ignore


def test_BaseDataGrabber_filter_single() -> None:
    """Test single-keyed element filter for BaseDataGrabber."""

    # Create concrete class
    class FilterDataGrabber(BaseDataGrabber):
        def get_item(self, subject):
            return {"BOLD": {}}

        def get_elements(self):
            return ["sub01", "sub02", "sub03"]

        def get_element_keys(self):
            return ["subject"]

    dg = FilterDataGrabber(datadir="/tmp", types=["BOLD"])
    with dg:
        assert "sub01" in list(dg.filter(["sub01"]))
        assert "sub02" not in list(dg.filter(["sub01"]))


def test_BaseDataGrabber_filter_multi() -> None:
    """Test multi-keyed element filter for BaseDataGrabber."""

    # Create concrete class
    class FilterDataGrabber(BaseDataGrabber):
        def get_item(self, subject):
            return {"BOLD": {}}

        def get_elements(self):
            return [
                ("sub01", "rest"),
                ("sub01", "movie"),
                ("sub02", "rest"),
                ("sub02", "movie"),
                ("sub03", "rest"),
                ("sub03", "movie"),
            ]

        def get_element_keys(self):
            return ["subject", "task"]

    dg = FilterDataGrabber(datadir="/tmp", types=["BOLD"])
    with dg:
        assert ("sub01", "rest") in list(
            dg.filter([("sub01", "rest")])  # type: ignore
        )
        assert ("sub01", "movie") not in list(
            dg.filter([("sub01", "rest")])  # type: ignore
        )
        assert ("sub02", "rest") not in list(
            dg.filter([("sub01", "rest")])  # type: ignore
        )
        assert ("sub02", "movie") not in list(
            dg.filter([("sub01", "rest")])  # type: ignore
        )
