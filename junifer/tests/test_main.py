"""Provide tests for junifer package."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import importlib


def test_import() -> None:
    """Test junifer import."""
    import junifer

    importlib.reload(junifer)
    print(junifer.__version__)
