"""Provide testing registry."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from ..pipeline import PipelineComponentRegistry
from .datagrabbers import (
    OasisVBMTestingDataGrabber,
    PartlyCloudyTestingDataGrabber,
    SPMAuditoryTestingDataGrabber,
)


# Register testing DataGrabbers
PipelineComponentRegistry().register(
    step="datagrabber",
    klass=OasisVBMTestingDataGrabber,
)

PipelineComponentRegistry().register(
    step="datagrabber",
    klass=SPMAuditoryTestingDataGrabber,
)

PipelineComponentRegistry().register(
    step="datagrabber",
    klass=PartlyCloudyTestingDataGrabber,
)
