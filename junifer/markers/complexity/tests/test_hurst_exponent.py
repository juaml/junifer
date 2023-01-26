"""Provide test for Hurst exponent."""

# Authors: Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
# License: AGPL

import os
from pathlib import Path

from nilearn.maskers import NiftiLabelsMasker

from junifer.data import load_parcellation
from junifer.datareader import DefaultDataReader
from junifer.markers import HurstExponent
from junifer.storage import SQLiteFeatureStorage
from junifer.testing.datagrabbers import SPMAuditoryTestingDatagrabber


# Set parcellation
PARCELLATION = "Schaefer100x17"


def test_compute() -> None:
    """Test HurstExponent compute()."""
    with SPMAuditoryTestingDatagrabber() as dg:
        # Fetch element
        element = dg["sub001"]
        # Fetch element data
        element_data = DefaultDataReader().fit_transform(element)
        # Initialize the marker
        marker = HurstExponent(parcellation=PARCELLATION)
        # Compute the marker
        feature_map = marker.fit_transform(element_data)

    # Load parcellation
    test_parcellation, _, _ = load_parcellation(PARCELLATION)
    # Compute the NiftiLabelsMasker
    test_masker = NiftiLabelsMasker(test_parcellation)
    test_ts = test_masker.fit_transform(element_data["BOLD"]["data"])
    _, n_roi = test_ts.shape

    # Assert the dimension of timeseries
    _, n_roi2 = feature_map["BOLD"]["data"].shape
    assert n_roi == n_roi2


def test_get_output_type() -> None:
    """Test HurstExponent get_output_type()."""
    marker = HurstExponent(parcellation=PARCELLATION)
    assert marker.get_output_type("BOLD") == "matrix"


def test_store(tmp_path: Path) -> None:
    """Test HurstExponent store().

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with SPMAuditoryTestingDatagrabber() as dg:
        # Fetch element
        element = dg["sub001"]
        # Fetch element data
        element_data = DefaultDataReader().fit_transform(element)
        # Initialize the marker
        marker = HurstExponent(parcellation=PARCELLATION)

        # Create storage
        # tmp_path = "/home/aomidvarnia/tmp"
        storage_uri = os.path.join(tmp_path, "test_hurst_exponent.sqlite")
        storage = SQLiteFeatureStorage(uri=storage_uri)
        # Compute the marker and store
        marker.fit_transform(input=element_data, storage=storage)
