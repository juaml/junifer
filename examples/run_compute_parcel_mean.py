"""
Compute Parcel Aggregation.
===========================

This example uses the ``ParcelAggregation`` marker to compute the mean of each
parcel using the Tian subcortical parcellation (scale I, 16 ROIs) for a 3D
NIfTI and the Schaefer parcellation (100 rois, 7 Yeo networks) for a 4D NIfTI.

Authors: Federico Raimondo, Synchon Mandal

License: BSD 3 clause
"""

from junifer.testing.datagrabbers import (
    ADHDTestingDataGrabber,
    UCLACNPVBMTestingDataGrabber,
)
from junifer.datagrabber import DataType
from junifer.datareader import DefaultDataReader
from junifer.markers import ParcelAggregation
from junifer.stats import AggFunc
from junifer.utils import configure_logging


###############################################################################
# Set the logging level to info to see extra information
configure_logging(level="INFO")

###############################################################################
# Perform parcel aggregation on VBM GM data (3D) from the UCLA CNP dataset
with UCLACNPVBMTestingDataGrabber() as dg:
    # Get the first element
    element = dg.get_elements()[0]
    # Read the element
    element_data = DefaultDataReader().fit_transform(dg[element])
    # Initialize marker
    marker = ParcelAggregation(
        parcellation="TianxS1x3TxMNInonlinear2009cAsym",
        method=AggFunc.Mean,
    )
    # Compute feature
    feature = marker.fit_transform(element_data)
    # Print the output
    print(feature.keys())
    print(feature["VBM_GM"]["aggregation"]["data"].shape)  # Shape is (1 x parcels)

###############################################################################
# Perform parcel aggregation on BOLD data (4D) from ADHD dataset
with ADHDTestingDataGrabber() as dg:
    # Get the first element
    element = dg.get_elements()[0]
    # Read the element
    element_data = DefaultDataReader().fit_transform(dg[element])
    # Initialize marker
    marker = ParcelAggregation(
        parcellation="Schaefer100x7",
        method=AggFunc.Mean,
        on=[DataType.BOLD],
    )
    # Compute feature
    feature = marker.fit_transform(element_data)
    # Print the output
    print(feature.keys())
    print(feature["BOLD"]["aggregation"]["data"].shape)  # Shape is (timepoints x parcels)
