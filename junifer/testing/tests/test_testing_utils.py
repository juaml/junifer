"""Provide tests for testing utils."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

import pytest

from junifer.testing import config_override
from junifer.utils import config


def test_config_override_unset() -> None:
    """Test config_override deletes a previously unset key."""
    assert config.get("testing.override") is None
    with config_override("testing.override", True):
        assert config.get("testing.override") is True
    assert "testing.override" not in config._config


def test_config_override_restore() -> None:
    """Test config_override restores a previously set value."""
    config.set("testing.override", 1)
    try:
        with config_override("testing.override", 2):
            assert config.get("testing.override") == 2
        assert config.get("testing.override") == 1
    finally:
        config.delete("testing.override")


def test_config_override_error() -> None:
    """Test config_override restores the state on error."""
    with pytest.raises(RuntimeError), config_override("testing.override", 3):
        raise RuntimeError()
    assert "testing.override" not in config._config
