"""Provide test for sample entropy."""

# Authors: Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
# License: AGPL

from pathlib import Path
import os

from nilearn.maskers import NiftiLabelsMasker

from junifer.data import load_parcellation
from junifer.datareader import DefaultDataReader
from junifer.markers import SampleEntropy
from junifer.storage import SQLiteFeatureStorage
from junifer.testing.datagrabbers import SPMAuditoryTestingDatagrabber


# Set parcellation
PARCELLATION = "Schaefer100x17"


def test_compute() -> None:
    """Test SampleEntropy compute()."""
    with SPMAuditoryTestingDatagrabber() as dg:
        # Fetch element
        element = dg["sub001"]
        # Fetch element data
        element_data = DefaultDataReader().fit_transform(element)
        # Initialize the marker
        marker = SampleEntropy(parcellation=PARCELLATION)
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
    """Test SampleEntropy get_output_type()."""
    marker = SampleEntropy(parcellation=PARCELLATION)
    assert marker.get_output_type("BOLD") == "matrix"


def test_store(tmp_path: Path) -> None:
    """Test SampleEntropy store().

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
        marker = SampleEntropy(parcellation=PARCELLATION)
        # Create storage
        storage_uri = os.path.join(
            tmp_path, 
            "test_sample_entropy.sqlite"
        )
        storage_uri = tmp_path / "test_sample_entropy.sqlite"
        storage = SQLiteFeatureStorage(uri=storage_uri)
        # Compute the marker and store
        marker.fit_transform(input=element_data, storage=storage)
