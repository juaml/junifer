"""Provide tests for base complexity marker."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import pytest


pytest.importorskip("neurokit2")

from junifer.markers.complexity.complexity_base import (
    ComplexityBase,
)


def test_base_complexity_marker_abstractness() -> None:
    """Test ComplexityBase is an abstract base class."""
    with pytest.raises(TypeError, match="abstract"):
        ComplexityBase()
