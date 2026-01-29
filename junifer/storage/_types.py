"""Provide common types for feature storage."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from enum import Enum


__all__ = ["MatrixKind"]


class MatrixKind(str, Enum):
    """Accepted matrix kind value."""

    UpperTriangle = "triu"
    LowerTriangle = "tril"
    Full = "full"
