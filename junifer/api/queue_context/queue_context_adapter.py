"""Define abstract base class for queue context adapter."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from abc import ABC, abstractmethod

from ...utils import raise_error


__all__ = ["QueueContextAdapter"]


class QueueContextAdapter(ABC):
    """Abstract base class for queue context adapter.

    For every interface that is required, one needs to provide a concrete
    implementation of this abstract class.

    """

    @abstractmethod
    def pre_run(self) -> str:
        """Return pre-run commands."""
        raise_error(
            msg="Concrete classes need to implement pre_run()",
            klass=NotImplementedError,
        )

    @abstractmethod
    def run(self) -> str:
        """Return run commands."""
        raise_error(
            msg="Concrete classes need to implement run()",
            klass=NotImplementedError,
        )

    @abstractmethod
    def pre_collect(self) -> str:
        """Return pre-collect commands."""
        raise_error(
            msg="Concrete classes need to implement pre_collect()",
            klass=NotImplementedError,
        )

    @abstractmethod
    def collect(self) -> str:
        """Return collect commands."""
        raise_error(
            msg="Concrete classes need to implement collect()",
            klass=NotImplementedError,
        )

    @abstractmethod
    def prepare(self) -> None:
        """Prepare assets for submission."""
        raise_error(
            msg="Concrete classes need to implement prepare()",
            klass=NotImplementedError,
        )
