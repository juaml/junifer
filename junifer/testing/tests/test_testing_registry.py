"""Provide tests for testing registry."""

import importlib

from junifer.pipeline import PipelineComponentRegistry


def test_testing_registry() -> None:
    """Test testing registry."""
    import junifer

    importlib.reload(junifer.pipeline.pipeline_component_registry)
    importlib.reload(junifer)

    step_components = PipelineComponentRegistry().step_components(
        "datagrabber"
    )
    assert "OasisVBMTestingDataGrabber" not in step_components
    assert "SPMAuditoryTestingDataGrabber" not in step_components
    assert "PartlyCloudyTestingDataGrabber" not in step_components

    importlib.import_module(junifer.testing.registry)

    updated_step_components = PipelineComponentRegistry().step_components(
        "datagrabber"
    )
    assert "OasisVBMTestingDataGrabber" in updated_step_components
    assert "SPMAuditoryTestingDataGrabber" in updated_step_components
    assert "PartlyCloudyTestingDataGrabber" in updated_step_components
