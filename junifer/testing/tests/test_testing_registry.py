"""Provide tests for testing registry."""

import importlib

from junifer.pipeline.registry import get_step_names


def test_testing_registry() -> None:
    """Test testing registry."""
    import junifer

    importlib.reload(junifer.pipeline.registry)
    importlib.reload(junifer)

    assert "OasisVBMTestingDataGrabber" not in get_step_names("datagrabber")
    assert "SPMAuditoryTestingDataGrabber" not in get_step_names("datagrabber")
    assert "PartlyCloudyTestingDataGrabber" not in get_step_names(
        "datagrabber"
    )
    importlib.reload(junifer.testing.registry)  # type: ignore

    assert "OasisVBMTestingDataGrabber" in get_step_names("datagrabber")
    assert "SPMAuditoryTestingDataGrabber" in get_step_names("datagrabber")
    assert "PartlyCloudyTestingDataGrabber" in get_step_names("datagrabber")
