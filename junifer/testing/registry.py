"""Provide testing registry."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from ..pipeline.registry import register
from .datagrabbers import (
    OasisVBMTestingDataGrabber,
    PartlyCloudyTestingDataGrabber,
    SPMAuditoryTestingDataGrabber,
)


# Register testing DataGrabbers
register(
    step="datagrabber",
    name="OasisVBMTestingDataGrabber",
    klass=OasisVBMTestingDataGrabber,
)

register(
    step="datagrabber",
    name="SPMAuditoryTestingDataGrabber",
    klass=SPMAuditoryTestingDataGrabber,
)

register(
    step="datagrabber",
    name="PartlyCloudyTestingDataGrabber",
    klass=PartlyCloudyTestingDataGrabber,
)
