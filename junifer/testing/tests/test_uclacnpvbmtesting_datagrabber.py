"""Provide tests for UCLACNPVBMTestingDataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

import nibabel as nib
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
