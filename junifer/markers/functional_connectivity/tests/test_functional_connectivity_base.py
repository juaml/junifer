"""Provide tests for base functional connectivity marker."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import pytest

# done to keep line length 79
import junifer.markers.functional_connectivity as fc


def test_base_functional_connectivity_marker_abstractness() -> None:
    """Test FunctionalConnectivityBase is an abstract base class."""
    with pytest.raises(TypeError, match="abstract"):
        fc.functional_connectivity_base.FunctionalConnectivityBase()
