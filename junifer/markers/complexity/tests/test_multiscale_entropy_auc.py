"""Provide test for the AUC of multiscale entropy."""

# Authors: Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

import pytest


pytest.importorskip("neurokit2")


from junifer.datagrabber import DataType
from junifer.datareader import DefaultDataReader
from junifer.markers.complexity import MultiscaleEntropyAUC
from junifer.storage import SQLiteFeatureStorage
from junifer.testing.datagrabbers import (
    PartlyCloudyTestingDataGrabber,
)


pytestmark = pytest.mark.external


# Set parcellation
PARCELLATION = "TianxS1x3TxMNInonlinear2009cAsym"


@pytest.fixture(scope="module")
def element_data() -> dict:
    """Load the data element once for all tests in the module.

    Returns
    -------
    dict
        The element data.

    """
    with PartlyCloudyTestingDataGrabber() as dg:
        # Fetch element
        element = dg["sub-01"]
        # Fetch element data
        return DefaultDataReader().fit_transform(element)


def test_compute(element_data: dict) -> None:
    """Test MultiscaleEntropyAUC compute().

    Parameters
    ----------
    element_data : dict
        The element data.

    """
    # Initialize the marker
    marker = MultiscaleEntropyAUC(parcellation=PARCELLATION)
    # Compute the marker
    feature_map = marker.fit_transform(element_data)
    # Assert the dimension of timeseries
    assert feature_map["BOLD"]["complexity"]["data"].ndim == 2


def test_storage_type() -> None:
    """Test MultiscaleEntropyAUC storage_type."""
    assert "vector" == MultiscaleEntropyAUC(
        parcellation=PARCELLATION
    ).storage_type(input_type=DataType.BOLD, output_feature="complexity")


def test_store(element_data: dict, tmp_path: Path) -> None:
    """Test MultiscaleEntropyAUC store().

    Parameters
    ----------
    element_data : dict
        The element data.
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    # Initialize the marker
    marker = MultiscaleEntropyAUC(parcellation=PARCELLATION)
    # Create storage
    storage = SQLiteFeatureStorage(
        uri=tmp_path / "test_multiscale_entropy_auc.sqlite"
    )
    # Compute the marker and store
    marker.fit_transform(input=element_data, storage=storage)
