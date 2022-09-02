"""Provide testing registry."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from ..api.registry import register
from .datagrabbers import OasisVBMTestingDatagrabber


# Register testing datagrabber
register(
    step="datagrabber",
    name="OasisVBMTestingDatagrabber",
    klass=OasisVBMTestingDatagrabber,
)
