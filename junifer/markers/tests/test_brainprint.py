"""Provide tests for BrainPrint."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import socket

import pytest

from junifer.datagrabber import DataladAOMICID1000
from junifer.datareader import DefaultDataReader
from junifer.markers import BrainPrint
from junifer.pipeline.utils import _check_freesurfer


@pytest.mark.parametrize(
    "feature, storage_type",
    [
        ("eigenvalues", "scalar_table"),
        ("areas", "vector"),
        ("volumes", "vector"),
        ("distances", "vector"),
    ],
)
def test_get_output_type(feature: str, storage_type: str) -> None:
    """Test BrainPrint get_output_type().

    Parameters
    ----------
    feature : str
        The parametrized feature name.
    storage_type : str
        The parametrized storage type.

    """
    assert storage_type == BrainPrint().get_output_type(
        input_type="FreeSurfer", output_feature=feature
    )


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
        # Compute marker
        feature_map = BrainPrint().fit_transform(element_data)
        # Assert the output keys
        assert {"eigenvalues", "areas", "volumes"} == set(feature_map.keys())
