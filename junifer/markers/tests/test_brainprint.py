"""Provide tests for BrainPrint."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import socket

import pytest

from junifer.datagrabber import DataladAOMICID1000
from junifer.datareader import DefaultDataReader
from junifer.markers import BrainPrint
from junifer.pipeline.utils import _check_freesurfer


def test_get_output_type() -> None:
    """Test BrainPrint get_output_type()."""
    marker = BrainPrint()
    assert marker.get_output_type("FreeSurfer") == "vector"


def test_validate() -> None:
    """Test BrainPrint validate()."""
    marker = BrainPrint()
    assert set(marker.validate(["FreeSurfer"])) == {"scalar_table", "vector"}


@pytest.mark.skipif(
    _check_freesurfer() is False, reason="requires FreeSurfer to be in PATH"
)
@pytest.mark.skipif(
    socket.gethostname() != "juseless",
    reason="only for juseless",
)
def test_compute() -> None:
    """Test BrainPrint compute()."""
    with DataladAOMICID1000(types="FreeSurfer") as dg:
        # Fetch element
        element = dg["sub-0001"]
        # Fetch element data
        element_data = DefaultDataReader().fit_transform(element)
        # Initialize the marker
        marker = BrainPrint()
        # Compute the marker
        feature_map = marker.fit_transform(element_data)
        # Assert the output keys
        assert {"eigenvalues", "areas", "volumes"} == set(feature_map.keys())
