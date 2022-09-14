"""Provide tests for testing registry."""

from junifer.api.registry import get_step_names


def test_testing_registry() -> None:
    """Test testing registry."""
    assert "OasisVBMTestingDatagrabber" not in get_step_names("datagrabber")
    assert "SPMAuditoryTestingDatagrabber" not in get_step_names("datagrabber")
    from junifer.testing import registry  # noqa

    assert "OasisVBMTestingDatagrabber" in get_step_names("datagrabber")
    assert "SPMAuditoryTestingDatagrabber" in get_step_names("datagrabber")
