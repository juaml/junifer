"""Provide tests for base functional connectivity marker."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import pytest

# done to keep line length 79
from junifer.markers.functional_connectivity import (
    functional_connectivity_base as fcb,
)


def test_base_functional_connectivity_marker_abstractness() -> None:
    """Test FunctionalConnectivityBase is an abstract base class."""
    with pytest.raises(TypeError, match="abstract"):
        fcb.FunctionalConnectivityBase()  # type: ignore
