"""Provide tests for testing registry."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

def test_testing_registry() -> None:
    """Test testing registry."""
    from junifer.pipeline import PipelineComponentRegistry

    assert not {
        "OasisVBMTestingDataGrabber",
        "SPMAuditoryTestingDataGrabber",
        "PartlyCloudyTestingDataGrabber",
    }.issubset(set(PipelineComponentRegistry().step_components("datagrabber")))

    from junifer.pipeline import PipelineComponentRegistry

    assert {
        "OasisVBMTestingDataGrabber",
        "SPMAuditoryTestingDataGrabber",
        "PartlyCloudyTestingDataGrabber",
    }.issubset(set(PipelineComponentRegistry().step_components("datagrabber")))
