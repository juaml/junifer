"""Provide tests for testing registry."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from junifer.pipeline import PipelineComponentRegistry
from junifer.testing.datagrabbers import (
    OasisVBMTestingDataGrabber,
    PartlyCloudyTestingDataGrabber,
    SPMAuditoryTestingDataGrabber,
)


def test_testing_registry() -> None:
    """Test testing registry."""
    for dg in [
        OasisVBMTestingDataGrabber,
        SPMAuditoryTestingDataGrabber,
        PartlyCloudyTestingDataGrabber,
    ]:
        PipelineComponentRegistry().register(
            step="datagrabber",
            klass=dg,
        )
    assert {
        "OasisVBMTestingDataGrabber",
        "SPMAuditoryTestingDataGrabber",
        "PartlyCloudyTestingDataGrabber",
    }.issubset(set(PipelineComponentRegistry().step_components("datagrabber")))
    for dg in [
        OasisVBMTestingDataGrabber,
        SPMAuditoryTestingDataGrabber,
        PartlyCloudyTestingDataGrabber,
    ]:
        PipelineComponentRegistry().deregister(
            step="datagrabber",
            klass=dg,
        )
