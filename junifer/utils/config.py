"""Provide junifer global configuration."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL
import os
from typing import Any

from .logging import logger
from .singleton import Singleton


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
        for t_var in os.environ:
            if t_var.startswith("JUNIFER_"):
                varname = t_var.replace("JUNIFER_", "")
                varname = varname.lower()
                varname.replace("_", ".")
                logger.debug(
                    f"Setting {varname} from environment to "
                    f"{os.environ[t_var]}"
                )
                self._config[varname] = os.environ[t_var]

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration parameter.

        Parameters
        ----------
        key : str
            The configuration key.

        default : Any, optional
            The default value to return if the key is not found (default None).

        Returns
        -------
        Any
            The configuration value.

        """
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration parameter.

        Parameters
        ----------
        key : str
            The configuration key.
        value : Any
            The configuration value.

        """
        logger.debug(f"Setting {key} to {value}")
        self._config[key] = value


config = ConfigManager()
