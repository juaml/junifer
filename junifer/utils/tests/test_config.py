"""Provide tests for ConfigManager."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from junifer.utils import config
from junifer.utils._config import ConfigManager


def test_config_manager_singleton() -> None:
    """Test that ConfigManager is a singleton."""
    config_mgr_1 = ConfigManager()
    config_mgr_2 = ConfigManager()
    assert id(config_mgr_1) == id(config_mgr_2)


def test_config_manager_get_set() -> None:
    """Test config getting and setting for ConfigManager."""
    # Get non-existing with default
    assert "mystery_machine" == config.get(
        key="scooby", default="mystery_machine"
    )
    # Set
    config.set(key="scooby", value="doo")
    # Get existing
    assert "doo" == config.get("scooby")
