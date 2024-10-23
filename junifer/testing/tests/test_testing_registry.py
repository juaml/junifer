"""Provide tests for testing registry."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from junifer.pipeline import PipelineComponentRegistry


def test_testing_registry() -> None:
    """Test testing registry."""
    assert {
        "OasisVBMTestingDataGrabber",
        "SPMAuditoryTestingDataGrabber",
        "PartlyCloudyTestingDataGrabber",
    }.issubset(set(PipelineComponentRegistry().step_components("datagrabber")))
