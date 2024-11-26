"""Provide junifer global configuration."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import os
from typing import Optional

from ..typing import ConfigVal
from .logging import logger
from .singleton import Singleton


__all__ = ["ConfigManager", "config"]


class ConfigManager(metaclass=Singleton):
    """Manage configuration parameters.

    Attributes
    ----------
    _config : dict
        Configuration parameters.

    """

    def __init__(self) -> None:
        """Initialize the class."""
        self._config = {}
        # Initial setup from process env
        self._reload()

    def _reload(self) -> None:
        """Reload env vars."""
        for t_var in os.environ:
            if t_var.startswith("JUNIFER_"):
                # Set correct type
                var_value = os.environ[t_var]
                # bool
                if var_value.lower() == "true":
                    var_value = True
                elif var_value.lower() == "false":
                    var_value = False
                # numeric
                else:
                    try:
                        var_value = int(var_value)
                    except ValueError:
                        try:
                            var_value = float(var_value)
                        except ValueError:
                            pass
                # Set value
                var_name = (
                    t_var.replace("JUNIFER_", "").lower().replace("_", ".")
                )
                logger.debug(
                    f"Setting `{var_name}` from environment to "
                    f"`{var_value}` (type: {type(var_value)})"
                )
                self._config[var_name] = var_value

    def get(self, key: str, default: Optional[ConfigVal] = None) -> ConfigVal:
        """Get configuration parameter.

        Parameters
        ----------
        key : str
            The configuration key to get.
        default : bool or int or float or None, optional
            The default value to return if the key is not found (default None).

        Returns
        -------
        bool or int or float
            The configuration value.

        """
        return self._config.get(key, default)

    def set(self, key: str, val: ConfigVal) -> None:
        """Set configuration parameter.

        Parameters
        ----------
        key : str
            The configuration key to set.
        val : bool or int or float
            The value to set ``key`` to.

        """
        logger.debug(f"Setting `{key}` to `{val}` (type: {type(val)})")
        self._config[key] = val

    def delete(self, key: str) -> None:
        """Delete configuration parameter.

        Parameters
        ----------
        key : str
            The configuration key to delete.

        """
        logger.debug(f"Deleting `{key}` from config")
        _ = self._config.pop(key)


# Initialize here to access from anywhere
config = ConfigManager()
