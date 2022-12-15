"""Provide test for parcel-aggregated (f)ALFF ."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

import nibabel as nib
import numpy as np
import pytest
from nilearn import datasets
from nilearn.image import concat_imgs, math_img, new_img_like, resample_to_img
from nilearn.maskers import NiftiLabelsMasker, NiftiMasker
from numpy.testing import assert_array_almost_equal, assert_array_equal
from scipy.stats import trim_mean

from junifer.datareader import DefaultDataReader
from junifer.markers.falff import AmplitudeLowFrequencyFluctuationParcels
from junifer.testing.datagrabbers import PartlyCloudyTestingDataGrabber
from junifer.pipeline.utils import _check_afni


def test_AmplitudeLowFrequencyFluctuationParcels_python():
    """Test AmplitudeLowFrequencyFluctuationParcels using python."""
    # Get the SPM auditory data:

    with PartlyCloudyTestingDataGrabber() as dg:
        input = dg["sub-01"]

    input = DefaultDataReader().fit_transform(input)
    # Create ParcelAggregation object
    marker = AmplitudeLowFrequencyFluctuationParcels(
        parcellation="Schaefer100x7", method="mean", use_afni=False,
        fractional=False)
    jun_values4d = marker.fit_transform(input)["BOLD"]

    assert jun_values4d["data"].ndim == 2


@pytest.mark.skipif(
    _check_afni() is False, reason="requires afni to be in PATH"
)
def test_AmplitudeLowFrequencyFluctuationParcels_afni():
    """Test AmplitudeLowFrequencyFluctuationParcels using afni."""
    # Get the SPM auditory data:

    with PartlyCloudyTestingDataGrabber() as dg:
        input = dg["sub-01"]

    input = DefaultDataReader().fit_transform(input)
    # Create ParcelAggregation object
    marker = AmplitudeLowFrequencyFluctuationParcels(
        parcellation="Schaefer100x7", method="mean", use_afni=True,
        fractional=False)
    jun_values4d = marker.fit_transform(input)["BOLD"]

    assert jun_values4d["data"].ndim == 2

    # Again, should be blazing fast
    jun_values4d = marker.fit_transform(input)["BOLD"]