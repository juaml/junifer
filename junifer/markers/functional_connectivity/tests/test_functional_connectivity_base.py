"""Provide tests for base functional connectivity marker."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import pytest

from junifer.markers.functional_connectivity.functional_connectivity_base import (
    FunctionalConnectivityBase,
)


def test_base_functional_connectivity_marker_abstractness() -> None:
    """Test FunctionalConnectivityBase is an abstract base class."""
    with pytest.raises(TypeError, match="abstract"):
        FunctionalConnectivityBase()
