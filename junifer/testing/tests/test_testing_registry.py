"""Provide tests for testing registry."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from junifer.pipeline import PipelineComponentRegistry
from junifer.testing.datagrabbers import (
    ADHDTestingDataGrabber,
    OasisVBMTestingDataGrabber,
    PartlyCloudyTestingDataGrabber,
    SPMAuditoryTestingDataGrabber,
    UCLACNPVBMTestingDataGrabber,
)


def test_testing_registry() -> None:
    """Test testing registry."""
    for dg in [
        ADHDTestingDataGrabber,
        OasisVBMTestingDataGrabber,
        SPMAuditoryTestingDataGrabber,
        PartlyCloudyTestingDataGrabber,
        UCLACNPVBMTestingDataGrabber,
    ]:
        PipelineComponentRegistry().register(
            step="datagrabber",
            klass=dg,
        )
    assert {
        "ADHDTestingDataGrabber",
        "OasisVBMTestingDataGrabber",
        "SPMAuditoryTestingDataGrabber",
        "PartlyCloudyTestingDataGrabber",
        "UCLACNPVBMTestingDataGrabber",
    }.issubset(set(PipelineComponentRegistry().step_components("datagrabber")))
    for dg in [
        ADHDTestingDataGrabber,
        OasisVBMTestingDataGrabber,
        SPMAuditoryTestingDataGrabber,
        PartlyCloudyTestingDataGrabber,
        UCLACNPVBMTestingDataGrabber,
    ]:
        PipelineComponentRegistry().deregister(
            step="datagrabber",
            klass=dg,
        )
