"""Provide abstract base class for pipeline data registry."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

from ..utils import raise_error
from ..utils.singleton import ABCSingleton


__all__ = ["BasePipelineDataRegistry"]


class BasePipelineDataRegistry(ABC, metaclass=ABCSingleton):
    """Abstract base class for pipeline data registry.

    For every interface that is required, one needs to provide a concrete
    implementation for this abstract class.

    Attributes
    ----------
    registry : dict
        Registry of available pipeline data.
    list : dict
        Keys of available pipeline data registry.

    """

    def __init__(self) -> None:
        """Initialize the class."""
        self._registry: Mapping[str, Any] = {}

    @property
    def data(self) -> Mapping[str, Any]:
        """Get available pipeline data."""
        return self._registry

    @property
    def list(self) -> list[str]:
        """List available pipeline data keys."""
        return sorted(self._registry.keys())

    @abstractmethod
    def register(self) -> None:
        """Register data."""
        raise_error(
            msg="Concrete classes need to implement register().",
            klass=NotImplementedError,
        )

    @abstractmethod
    def deregister(self) -> None:
        """De-register data."""
        raise_error(
            msg="Concrete classes need to implement deregister().",
            klass=NotImplementedError,
        )

    @abstractmethod
    def load(self) -> Any:
        """Load data."""
        raise_error(
            msg="Concrete classes need to implement load().",
            klass=NotImplementedError,
        )

    @abstractmethod
    def get(self) -> Any:
        """Get tailored data for a target."""
        raise_error(
            msg="Concrete classes need to implement get().",
            klass=NotImplementedError,
        )
