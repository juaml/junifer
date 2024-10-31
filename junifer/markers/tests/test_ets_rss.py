"""Provide test for root sum of squares of edgewise timeseries."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
#          Nicolás Nieto <n.nieto@fz-juelich.de>
#          Sami Hamdan <s.hamdan@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

from nilearn.maskers import NiftiLabelsMasker

from junifer.data import ParcellationRegistry
from junifer.datareader import DefaultDataReader
from junifer.markers.ets_rss import RSSETSMarker
from junifer.storage import SQLiteFeatureStorage
from junifer.testing.datagrabbers import PartlyCloudyTestingDataGrabber


# Set parcellation
PARCELLATION = "TianxS1x3TxMNInonlinear2009cAsym"


def test_compute() -> None:
    """Test RSS ETS compute()."""
    with PartlyCloudyTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        # Compute the RSSETSMarker
        rss_ets = RSSETSMarker(parcellation=PARCELLATION).compute(
            element_data["BOLD"]
        )

        # Compare with nilearn
        # Load testing parcellation
        test_parcellation, _ = ParcellationRegistry().get(
            parcellations=[PARCELLATION],
            target_data=element_data["BOLD"],
        )
        # Extract timeseries
        nifti_labels_masker = NiftiLabelsMasker(labels_img=test_parcellation)
        extacted_timeseries = nifti_labels_masker.fit_transform(
            element_data["BOLD"]["data"]
        )
        # Assert the dimension of timeseries
        assert extacted_timeseries.shape[0] == len(rss_ets["rss_ets"]["data"])


def test_get_output_type() -> None:
    """Test RSS ETS get_output_type()."""
    assert "timeseries" == RSSETSMarker(
        parcellation=PARCELLATION
    ).get_output_type(input_type="BOLD", output_feature="rss_ets")


def test_store(tmp_path: Path) -> None:
    """Test RSS ETS store().

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with PartlyCloudyTestingDataGrabber() as dg:
        # Get element data
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        # Create storage
        storage = SQLiteFeatureStorage(tmp_path / "test_rss_ets.sqlite")
        # Compute the RSSETSMarker and store
        _ = RSSETSMarker(parcellation=PARCELLATION).fit_transform(
            input=element_data, storage=storage
        )
        # Retrieve features
        features = storage.list_features()
        # Check marker name
        assert any(
            x["name"] == "BOLD_RSSETSMarker_rss_ets" for x in features.values()
        )
