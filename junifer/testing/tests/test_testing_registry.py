"""Provide tests for testing registry."""


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
