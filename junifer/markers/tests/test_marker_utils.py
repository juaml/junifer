"""Provide test for marker utility functions."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
#          Nicolás Nieto <n.nieto@fz-juelich.de>
#          Sami Hamdan <s.hamdan@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import numpy as np
import pytest

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

    # test without labels
    edge_ts, _ = _ets(bold_ts)
    assert edge_ts.shape == (n_time, n_edges)

    # test with labels
    roi_labels = [f"Label_{x}" for x in range(n_rois)]
    edge_ts, edge_labels = _ets(bold_ts, roi_labels)
    assert edge_ts.shape == (n_time, n_edges)
    assert edge_labels is not None
    assert len(edge_labels) == n_edges


def test_ets_incorrect_label_list() -> None:
    """Test edge-wise timeseries computing function with incorrect labels."""
    bold_ts = np.arange(30).reshape(10, 3)
    # one label is missing, the bold time series suggests three ROIs
    roi_labels = ["label 1", "label 2"]

    with pytest.raises(
        ValueError, match="List of roi names does not correspond"
    ):
        _ets(bold_ts, roi_labels)
