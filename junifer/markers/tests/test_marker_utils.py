"""Provide test for marker utility functions."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
#          Nicolás Nieto <n.nieto@fz-juelich.de>
#          Sami Hamdan <s.hamdan@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

import nibabel as nib
import numpy as np
import pytest

from junifer.markers.utils import _ets, _save_mask
from junifer.pipeline import WorkDirManager


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


def test_save_mask(tmp_path: Path) -> None:
    """Test saving masks in the element directory, named by their content.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    workdir_mgr = WorkDirManager()
    workdir_mgr.workdir = tmp_path
    data = np.zeros((3, 4, 5), dtype=np.int8)
    data[1, 1:3, 2:4] = 1
    mask = nib.Nifti1Image(data, np.eye(4))
    path = _save_mask(mask, prefix="test_mask")
    # In the element directory, with the voxels in the mask
    assert path.parent == workdir_mgr.elementdir
    assert path.name.startswith("test_mask_")
    assert np.array_equal(np.asarray(nib.load(path).dataobj), data)
    # The same mask (another image) has the same path, a different one not
    assert (
        _save_mask(nib.Nifti1Image(data.copy(), np.eye(4)), prefix="test_mask")
        == path
    )
    other = data.copy()
    other[0, 0, 0] = 1
    assert (
        _save_mask(nib.Nifti1Image(other, np.eye(4)), prefix="test_mask")
        != path
    )
    # Deleted with the element directory
    workdir_mgr.cleanup_elementdir()
    assert not path.exists()
