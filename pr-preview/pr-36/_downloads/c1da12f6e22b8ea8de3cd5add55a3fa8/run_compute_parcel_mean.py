"""
Computer Parcel Aggregation.
============================

This example uses a ParcelAggregation marker to compute the mean of each parcel
using the Schaefer parcellations (100 rois, 7 Yeo networks) for both a 3D and
4D nifti

Authors: Federico Raimondo

License: BSD 3 clause
"""

import nilearn

from junifer.markers.parcel_aggregation import ParcelAggregation
from junifer.utils import configure_logging


###############################################################################
# Set the logging level to info to see extra information
configure_logging(level="INFO")


###############################################################################
# Load the VBM GM data (3d):
# - Fetch the Oasis dataset
oasis_dataset = nilearn.datasets.fetch_oasis_vbm(n_subjects=1)
vbm_fname = oasis_dataset.gray_matter_maps[0]
vbm_img = nilearn.image.load_img(vbm_fname)

###############################################################################
# Load the functional data (4d):
# - Fetch the SPM auditory dataset
# - Concatenate the functional data into one 4D image
s_func_data = nilearn.datasets.fetch_spm_auditory()
fmri_img = nilearn.image.concat_imgs(s_func_data.func)

###############################################################################
# Define the marker
marker = ParcelAggregation(parcellation="Schaefer100x7", method="mean")

###############################################################################
# Prepare the input
input = {
    "BOLD": {"data": fmri_img, "meta": {"element": "subject1"}},
    "VBM_GM": {"data": vbm_img, "meta": {"element": "subject1"}},
}

###############################################################################
# Fit transform the data
out = marker.fit_transform(input)

###############################################################################
# Check the results

print(out.keys())
print(out["VBM_GM"]["data"].shape)  # Shape is (1 x parcels)

print(out.keys())
print(out["BOLD"]["data"].shape)  # Shape is (timepoints x parcels)
