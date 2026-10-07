"""
Computer Parcel Aggregation.
============================

This example uses the ``ParcelAggregation`` marker to compute the mean of each
parcel using the Schaefer parcellations (100 rois, 7 Yeo networks) for both 3D
and 4D NIfTI.

Authors: Federico Raimondo, Synchon Mandal

License: BSD 3 clause
"""

from junifer.testing.datagrabbers import (
    OasisVBMTestingDataGrabber,
    SPMAuditoryTestingDataGrabber,
)
from junifer.datareader import DefaultDataReader
from junifer.markers import ParcelAggregation
from junifer.utils import configure_logging


###############################################################################
# Set the logging level to info to see extra information
configure_logging(level="INFO")

###############################################################################
# Perform parcel aggregation on VBM GM data (3D) from OASIS dataset
with OasisVBMTestingDataGrabber() as dg:
    # Get the first element
    element = dg.get_elements()[0]
    # Read the element
    element_data = DefaultDataReader().fit_transform(dg[element])
    # Initialize marker
    marker = ParcelAggregation(parcellation="Schaefer100x7", method="mean")
    # Compute feature
    feature = marker.fit_transform(element_data)
    # Print the output
    print(feature.keys())
    print(feature["VBM_GM"]["aggregation"]["data"].shape)  # Shape is (1 x parcels)

###############################################################################
# Perform parcel aggregation on BOLD data (4D) from SPM Auditory dataset
with SPMAuditoryTestingDataGrabber() as dg:
    # Get the first element
    element = dg.get_elements()[0]
    # Read the element
    element_data = DefaultDataReader().fit_transform(dg[element])
    # Initialize marker
    marker = ParcelAggregation(
        parcellation="Schaefer100x7", method="mean", on="BOLD"
    )
    # Compute feature
    feature = marker.fit_transform(element_data)
    # Print the output
    print(feature.keys())
    print(feature["BOLD"]["aggregation"]["data"].shape)  # Shape is (timepoints x parcels)
