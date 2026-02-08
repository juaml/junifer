"""Define abstract base class for queue context adapter."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import sys


if sys.version_info < (3, 12):  # pragma: no cover
    from typing_extensions import TypedDict
else:
    from typing import TypedDict

if sys.version_info < (3, 11):  # pragma: no cover
    from typing_extensions import Required
else:
    from typing import Required

from abc import ABC, abstractmethod
from enum import Enum

from pydantic import BaseModel, ConfigDict

from ...utils import raise_error


__all__ = ["EnvKind", "EnvShell", "QueueContextAdapter", "QueueContextEnv"]


class EnvKind(str, Enum):
    """Accepted Python environment kind."""

    Venv = "venv"
    Conda = "conda"
    Local = "local"


class EnvShell(str, Enum):
    """Accepted environment shell."""

    Bash = "bash"
    Zsh = "zsh"


class QueueContextEnv(TypedDict, total=False):
    """Accepted environment configuration for queue context."""

    kind: Required[EnvKind]
    name: str
    shell: Required[EnvShell]


class QueueContextAdapter(BaseModel, ABC):
    """Abstract base class for queue context adapter.

    For every queue context, one needs to provide a concrete
    implementation of this abstract class.

    """

    model_config = ConfigDict(
        use_enum_values=True,
        extra="allow",
    )

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
