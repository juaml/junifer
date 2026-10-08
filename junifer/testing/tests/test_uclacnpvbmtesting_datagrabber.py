"""Provide tests for UCLACNPVBMTestingDataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

import nibabel as nib
import numpy as np
import pytest
from numpy.testing import assert_array_almost_equal
from templateflow import api as tflow

from junifer.testing.datagrabbers import UCLACNPVBMTestingDataGrabber


pytestmark = pytest.mark.external


def test_UCLACNPVBMTestingDataGrabber() -> None:
    """Test UCLACNPVBMTestingDataGrabber."""
    with UCLACNPVBMTestingDataGrabber() as dg:
        elements = dg.get_elements()
        assert len(elements) == 10
        out = dg[elements[0]]
        assert "VBM_GM" in out
        assert out["VBM_GM"]["path"].is_file()
        assert out["VBM_GM"]["space"] == "MNI152NLin2009cAsym"

        # Resampled to the templateflow grid, so templates and masks do not
        # need resampling
        img = nib.load(out["VBM_GM"]["path"])
        template = nib.load(
            tflow.get(
                "MNI152NLin2009cAsym",
                resolution=2,
                suffix="T1w",
                desc=None,
                extension="nii.gz",
            )
        )
        assert img.shape == template.shape[:3]
        assert_array_almost_equal(img.affine, template.affine)

        participants = dg.get_participants()
        assert list(participants.index) == elements
        assert {"age", "gender"} <= set(participants.columns)


def test_UCLACNPVBMTestingDataGrabber_native() -> None:
    """Test UCLACNPVBMTestingDataGrabber at the native resolution."""
    with UCLACNPVBMTestingDataGrabber(resolution=1) as dg:
        out = dg[dg.get_elements()[0]]
        # No resampling at the native resolution
        assert out["VBM_GM"]["path"].name.endswith("_probtissue.nii.gz")
        assert nib.load(out["VBM_GM"]["path"]).shape == (193, 229, 193)


def test_UCLACNPVBMTestingDataGrabber_resample() -> None:
    """Test UCLACNPVBMTestingDataGrabber resampling to a new resolution."""
    with UCLACNPVBMTestingDataGrabber(resolution=4) as dg:
        element = dg.get_elements()[0]
        # Remove the cached map so it is resampled again (the CI image only
        # has the default resolution)
        native = dg._paths[element]
        cached = native.with_name(
            native.name.replace(".nii.gz", "_res-4mm.nii")
        )
        cached.unlink(missing_ok=True)

        out = dg[element]
        assert out["VBM_GM"]["path"] == cached
        img = nib.load(cached)
        assert img.shape == (49, 58, 49)
        assert img.get_data_dtype() == np.float32
        expected_affine = np.diag([4.0, 4.0, 4.0, 1.0])
        expected_affine[:3, 3] = [-97.5, -133.5, -79.5]
        assert_array_almost_equal(img.affine, expected_affine)

        # Cached, so it is not resampled again
        mtime = cached.stat().st_mtime_ns
        assert dg[element]["VBM_GM"]["path"] == cached
        assert cached.stat().st_mtime_ns == mtime
