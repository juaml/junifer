"""Provide tests for base temporal SNR marker."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL

import pytest

# done to keep line length 79
from junifer.markers.temporal_snr import temporal_snr_base as tsb


def test_base_temporal_snr_marker_abstractness() -> None:
    """Test TemporalSNRBase is an abstract base class."""
    with pytest.raises(TypeError, match="abstract"):
        tsb.TemporalSNRBase()
