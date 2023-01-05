"""Provide tests for base temporal SNR marker."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL

import pytest

# done to keep line length 79
import junifer.markers.temporal_snr as tsnr


def test_base_temporal_snr_marker_abstractness() -> None:
    """Test TemporalSNRBase is an abstract base class."""
    with pytest.raises(TypeError, match="abstract"):
        tsnr.temporal_snr_base.TemporalSNRBase()
