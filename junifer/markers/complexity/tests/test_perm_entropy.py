"""Provide test for permutation entropy."""

# Authors: Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

import pytest


pytest.importorskip("neurokit2")

from junifer.datareader import DefaultDataReader
from junifer.markers.complexity import PermEntropy
from junifer.pipeline.utils import _check_ants
from junifer.storage import SQLiteFeatureStorage
from junifer.testing.datagrabbers import (
    SPMAuditoryTestingDataGrabber,
)


# Set parcellation
PARCELLATION = "Schaefer100x17"


@pytest.mark.skipif(
    _check_ants() is False, reason="requires ANTs to be in PATH"
)
def test_compute() -> None:
    """Test PermEntropy compute()."""
    with SPMAuditoryTestingDataGrabber() as dg:
        # Fetch element
        element = dg["sub001"]
        # Fetch element data
        element_data = DefaultDataReader().fit_transform(element)
        # Initialize the marker
        marker = PermEntropy(parcellation=PARCELLATION)
        # Compute the marker
        feature_map = marker.fit_transform(element_data)
        # Assert the dimension of timeseries
        assert feature_map["BOLD"]["complexity"]["data"].ndim == 2


def test_get_output_type() -> None:
    """Test PermEntropy get_output_type()."""
    assert "vector" == PermEntropy(parcellation=PARCELLATION).get_output_type(
        input_type="BOLD", output_feature="complexity"
    )


@pytest.mark.skipif(
    _check_ants() is False, reason="requires ANTs to be in PATH"
)
def test_store(tmp_path: Path) -> None:
    """Test PermEntropy store().

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with SPMAuditoryTestingDataGrabber() as dg:
        # Fetch element
        element = dg["sub001"]
        # Fetch element data
        element_data = DefaultDataReader().fit_transform(element)
        # Initialize the marker
        marker = PermEntropy(parcellation=PARCELLATION)
        # Create storage
        storage = SQLiteFeatureStorage(
            uri=tmp_path / "test_perm_entropy.sqlite"
        )
        # Compute the marker and store
        marker.fit_transform(input=element_data, storage=storage)
