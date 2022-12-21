"""Provide testing registry."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from ..pipeline.registry import register
from .datagrabbers import (
    OasisVBMTestingDatagrabber,
    PartlyCloudyTestingDataGrabber,
    SPMAuditoryTestingDatagrabber,
)


# Register testing datagrabber
register(
    step="datagrabber",
    name="OasisVBMTestingDatagrabber",
    klass=OasisVBMTestingDatagrabber,
)

register(
    step="datagrabber",
    name="SPMAuditoryTestingDatagrabber",
    klass=SPMAuditoryTestingDatagrabber,
)

register(
    step="datagrabber",
    name="PartlyCloudyTestingDataGrabber",
    klass=PartlyCloudyTestingDataGrabber,
)
