"""Provide tests for the ALFF and fALFF computation with masks."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from pathlib import Path

import nibabel as nib
import numpy as np
import pytest
from numpy.testing import assert_allclose, assert_array_equal

from junifer.markers.falff._afni_falff import AFNIALFF
from junifer.markers.falff._junifer_falff import JuniferALFF
from junifer.pipeline import WorkDirManager
from junifer.pipeline.utils import _check_afni


def _save(data: np.ndarray, path: Path, tr: float = 2.0) -> Path:
    """Save data as NIfTI, with the TR in the header for 4D data."""
    img = nib.Nifti1Image(data, np.eye(4))
    if data.ndim == 4:
        img.header.set_zooms((1.0, 1.0, 1.0, tr))
    nib.save(img, path)
    return path


def _data(tmp_path: Path) -> tuple[Path, Path, np.ndarray]:
    """Create BOLD data and a mask of half of the voxels."""
    data = np.random.default_rng(0).normal(size=(6, 6, 6, 100)) + 100
    bold_path = _save(data.astype(np.float32), tmp_path / "bold.nii")
    mask = np.zeros((6, 6, 6), dtype=np.uint8)
    mask[3:] = 1
    mask_path = _save(mask, tmp_path / "mask.nii")
    return bold_path, mask_path, mask.astype(bool)


@pytest.mark.parametrize(
    "estimator",
    [
        JuniferALFF,
        pytest.param(
            AFNIALFF,
            marks=pytest.mark.skipif(
                _check_afni() is False, reason="requires AFNI to be in PATH"
            ),
        ),
    ],
)
def test_ALFF_mask(
    estimator: type[JuniferALFF | AFNIALFF], tmp_path: Path
) -> None:
    """Test the ALFF and fALFF computation is restricted to the mask.

    The values are computed for each voxel, so inside the mask they are the
    same as without mask, and outside the mask they are 0.

    Parameters
    ----------
    estimator : JuniferALFF or AFNIALFF
        The ALFF estimator to test.
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    WorkDirManager().workdir = tmp_path
    bold_path, mask_path, mask = _data(tmp_path)
    kwargs = {"highpass": 0.01, "lowpass": 0.1, "tr": 2.0}
    masked = estimator().compute(bold_path, mask_path=mask_path, **kwargs)
    unmasked = estimator().compute(bold_path, **kwargs)
    for i_map in range(2):  # ALFF and fALFF
        t_masked = masked[i_map].get_fdata()
        t_unmasked = unmasked[i_map].get_fdata()
        assert_array_equal(t_masked[~mask], 0)
        assert (t_masked[mask] > 0).all()
        assert_allclose(t_masked[mask], t_unmasked[mask], rtol=1e-6)


@pytest.mark.skipif(
    _check_afni() is False, reason="requires AFNI to be in PATH"
)
def test_AFNIALFF_no_time_series(tmp_path: Path) -> None:
    """Test 3dRSFC does not output the bandpassed time series.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    WorkDirManager().workdir = tmp_path
    bold_path, mask_path, _ = _data(tmp_path)
    alff_path = AFNIALFF().compute(
        bold_path, highpass=0.01, lowpass=0.1, tr=2.0, mask_path=mask_path
    )[2]
    # Only the parameters (ALFF, fALFF and mALFF) are in the output directory
    outputs = {x.name for x in alff_path.parent.iterdir()}
    assert not any("_LFF+" in x for x in outputs)
    assert any("_ALFF+" in x for x in outputs)
