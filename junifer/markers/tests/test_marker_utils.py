"""Provide test for marker utility functions."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
#          Nicolás Nieto <n.nieto@fz-juelich.de>
#          Sami Hamdan <s.hamdan@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import numpy as np

from junifer.markers.utils import _ets


def test_ets() -> None:
    """Test edge-wise timeseries computing function."""
    bold_ts = np.array(
        [
            [x + 1 for x in range(20)],
            [x + 2 for x in range(20)],
            [x + 3 for x in range(20)],
            [x + 4 for x in range(20)],
        ]
    ).T

    n_time, n_rois = bold_ts.shape
    n_edges = int(n_rois * (n_rois - 1) / 2)

    edge_ts = _ets(bold_ts)
    assert edge_ts.shape == (n_time, n_edges)
