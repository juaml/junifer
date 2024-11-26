"""Provide tests for ConfigManager."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import os

import pytest

from junifer.typing import ConfigVal
from junifer.utils import config
from junifer.utils._config import ConfigManager


def test_config_manager_singleton() -> None:
    """Test that ConfigManager is a singleton."""
    config_mgr_1 = ConfigManager()
    config_mgr_2 = ConfigManager()
    assert id(config_mgr_1) == id(config_mgr_2)


def test_config_manager() -> None:
    """Test config operations for ConfigManager."""
    # Get non-existing with default
    assert config.get(key="scooby") is None
    # Set
    config.set(key="scooby", val=True)
    # Get existing
    assert config.get("scooby")
    # Delete
    config.delete("scooby")
    # Get non-existing with default
    assert config.get(key="scooby") is None


@pytest.mark.parametrize(
    "val, expected_val",
    [("TRUE", True), ("FALSE", False), ("1", 1), ("0.0", 0.0)],
)
def test_config_manager_env_reload(val: str, expected_val: ConfigVal) -> None:
    """Test config parsing from env reload.

    Parameters
    ----------
    val : str
        The parametrized values.
    expected_val : bool or int or float
        The parametrized expected value.

    """
    # Set env var
    os.environ["JUNIFER_TESTME"] = val
    # Check
    config._reload()
    assert config.get("testme") == expected_val
    # Cleanup
    del os.environ["JUNIFER_TESTME"]
    config.delete("testme")
