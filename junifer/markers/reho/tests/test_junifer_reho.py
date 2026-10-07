"""Provide tests for ReHo computation using junifer."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from pathlib import Path

import nibabel as nib
import numpy as np
import pytest
import scipy as sp
from numpy.testing import assert_allclose, assert_array_equal

from junifer.markers.reho._afni_reho import AFNIReHo
from junifer.markers.reho._junifer_reho import JuniferReHo, _rank_with_ties
from junifer.pipeline import WorkDirManager
from junifer.pipeline.utils import _check_afni


def _tied_rank_corrections(ranks: np.ndarray) -> np.ndarray:
    """Compute tied rank corrections one time series at a time."""
    out = np.zeros(ranks.shape[:-1])
    for idx in np.ndindex(ranks.shape[:-1]):
        _, tie_count = np.unique(ranks[idx], return_counts=True)
        out[idx] = np.sum(tie_count**3 - tie_count)
    return out


@pytest.mark.parametrize(
    "shape, scale",
    [
        ((4, 3, 2, 50), 3),  # many ties
        ((3, 3, 3, 30), 100),  # few ties
        ((2, 2, 2, 10), 0),  # all values tied
    ],
)
def test_rank_with_ties(shape: tuple[int, ...], scale: float) -> None:
    """Test ranking with ties against scipy.

    Parameters
    ----------
    shape : tuple of int
        The shape of the data.
    scale : float
        The scale of the data before rounding.

    """
    data = np.round(np.random.default_rng(0).normal(size=shape) * scale)
    ranks, tied_rank_corrections = _rank_with_ties(data)
    expected_ranks = sp.stats.rankdata(data, axis=-1)
    assert_array_equal(ranks, expected_ranks)
    assert_array_equal(
        tied_rank_corrections, _tied_rank_corrections(expected_ranks)
    )


def test_rank_with_ties_nan() -> None:
    """Test NaN propagates to the whole time series."""
    data = np.array([[1.0, np.nan, 2.0], [1.0, 3.0, 2.0]])
    ranks, tied_rank_corrections = _rank_with_ties(data)
    assert np.isnan(ranks[0]).all()
    assert np.isnan(tied_rank_corrections[0])
    assert_array_equal(ranks[1], [1, 3, 2])
    assert tied_rank_corrections[1] == 0


def _save(data: np.ndarray, path: Path) -> Path:
    """Save data as NIfTI."""
    nib.save(nib.Nifti1Image(data, np.eye(4)), path)
    return path


def test_JuniferReHo_nan(tmp_path: Path) -> None:
    """Test NaN time series do not give valid ReHo values.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    WorkDirManager().workdir = tmp_path
    data = np.random.default_rng(0).normal(size=(7, 7, 7, 20))
    data[3, 3, 3, 5] = np.nan
    bold_path = _save(data.astype(np.float32), tmp_path / "bold_nan.nii")
    mask_path = _save(np.ones((7, 7, 7), dtype=np.uint8), tmp_path / "m.nii")

    # With a mask including the NaN voxel, every neighbourhood with it is NaN
    reho = JuniferReHo().compute(bold_path, mask_path=mask_path)[0]
    reho = reho.get_fdata()
    assert np.isnan(reho[2:5, 2:5, 2:5]).all()
    reho[2:5, 2:5, 2:5] = 0
    assert np.isfinite(reho).all()

    # Without mask, the NaN voxel is excluded as AFNI's 3dReHo does
    reho = JuniferReHo().compute(bold_path)[0].get_fdata()
    assert np.isfinite(reho).all()
    assert reho[3, 3, 3] == 0


def test_JuniferReHo_mask(tmp_path: Path) -> None:
    """Test ReHo is restricted to the mask.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    WorkDirManager().workdir = tmp_path
    data = np.random.default_rng(0).normal(size=(7, 7, 7, 20))
    bold_path = _save(data.astype(np.float32), tmp_path / "bold.nii")
    mask = np.ones((7, 7, 7), dtype=np.uint8)
    mask[:3] = 0
    mask_path = _save(mask, tmp_path / "mask.nii")

    masked = JuniferReHo().compute(bold_path, mask_path=mask_path)[0]
    masked = masked.get_fdata()
    unmasked = JuniferReHo().compute(bold_path)[0].get_fdata()
    # Outside the mask is 0
    assert (masked[:3] == 0).all()
    # Next to the mask boundary, neighbours outside the mask are excluded
    assert not np.allclose(masked[3, 1:-1, 1:-1], unmasked[3, 1:-1, 1:-1])
    # Far from the mask boundary, nothing changes
    assert_array_equal(masked[4:-1, 1:-1, 1:-1], unmasked[4:-1, 1:-1, 1:-1])


@pytest.mark.external
@pytest.mark.skipif(
    _check_afni() is False, reason="requires AFNI to be in PATH"
)
@pytest.mark.parametrize("nneigh", [7, 19, 27])
@pytest.mark.parametrize("use_mask", [False, True])
def test_JuniferReHo_vs_AFNI(
    tmp_path: Path, nneigh: int, use_mask: bool
) -> None:
    """Test junifer and AFNI give the same ReHo map.

    The data covers the edges of the volume, fully tied neighbourhoods (the
    denominator of KCC is 0), voxels with all-zero time series and ties.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    nneigh : int
        The number of voxels in the neighbourhood.
    use_mask : bool
        Whether to use a mask.

    """
    WorkDirManager().workdir = tmp_path
    data = np.round(
        np.random.default_rng(0).normal(size=(9, 8, 7, 25)) * 3
    ).astype(np.float32)
    # Constant time series: fully tied neighbourhoods
    data[:4, :4, :4] = 5
    # All-zero time series: outside AFNI's implicit mask
    data[6:, 5:, 4:] = 0
    bold_path = _save(data, tmp_path / "bold.nii")
    mask_path = None
    if use_mask:
        mask = np.ones(data.shape[:3], dtype=np.uint8)
        mask[:, :, 0] = 0
        mask[4, 4, 3] = 0
        mask_path = _save(mask, tmp_path / "mask.nii")

    junifer_reho = JuniferReHo().compute(
        bold_path, nneigh=nneigh, mask_path=mask_path
    )[0]
    afni_reho = AFNIReHo().compute(
        bold_path, nneigh=nneigh, mask_path=mask_path
    )[0]
    assert_allclose(
        junifer_reho.get_fdata(),
        np.squeeze(afni_reho.get_fdata()),
        atol=1e-6,
    )
