"""Provide tests for testing registry."""

from junifer.api.registry import get_step_names
import importlib


def test_testing_registry() -> None:
    """Test testing registry."""
    import junifer
    importlib.reload(junifer.api.registry)
    importlib.reload(junifer)

    assert "OasisVBMTestingDatagrabber" not in get_step_names("datagrabber")
    assert "SPMAuditoryTestingDatagrabber" not in get_step_names("datagrabber")
    importlib.reload(junifer.testing.registry)

    assert "OasisVBMTestingDatagrabber" in get_step_names("datagrabber")
    assert "SPMAuditoryTestingDatagrabber" in get_step_names("datagrabber")
