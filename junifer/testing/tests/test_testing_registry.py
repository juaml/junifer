"""Provide tests for testing registry."""

import importlib

from junifer.pipeline.registry import get_step_names


def test_testing_registry() -> None:
    """Test testing registry."""
    import junifer

    importlib.reload(junifer.pipeline.registry)
    importlib.reload(junifer)

    assert "OasisVBMTestingDatagrabber" not in get_step_names("datagrabber")
    assert "SPMAuditoryTestingDatagrabber" not in get_step_names("datagrabber")
    importlib.reload(junifer.testing.registry)  # type: ignore

    assert "OasisVBMTestingDatagrabber" in get_step_names("datagrabber")
    assert "SPMAuditoryTestingDatagrabber" in get_step_names("datagrabber")
