"""Provide test for root sum of squares of edgewise timeseries."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
#          Nicolás Nieto <n.nieto@fz-juelich.de>
#          Sami Hamdan <s.hamdan@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

from nilearn import image
from nilearn.maskers import NiftiLabelsMasker

from junifer.data import load_parcellation
from junifer.markers.ets_rss import RSSETSMarker
from junifer.storage import SQLiteFeatureStorage
from junifer.testing.datagrabbers import SPMAuditoryTestingDatagrabber


# Set parcellation
PARCELLATION = "Schaefer100x17"


def test_compute() -> None:
    """Test RSS ETS compute()."""
    with SPMAuditoryTestingDatagrabber() as dg:
        # Fetch element
        out = dg["sub001"]
        # Load BOLD image
        niimg = image.load_img(str(out["BOLD"]["path"].absolute()))
        # Create input data
        input_dict = {"data": niimg, "path": out["BOLD"]["path"]}
        # Compute the RSSETSMarker
        ets_rss_marker = RSSETSMarker(parcellation=PARCELLATION)
        new_out = ets_rss_marker.compute(input_dict)

        # Load parcellation
        test_parcellation, _, _ = load_parcellation(PARCELLATION)
        # Compute the NiftiLabelsMasker
        test_masker = NiftiLabelsMasker(test_parcellation)
        test_ts = test_masker.fit_transform(niimg)
        # Assert the dimension of timeseries
        n_time, _ = test_ts.shape
        assert n_time == len(new_out["data"])


def test_get_output_type() -> None:
    """Test RSS ETS get_output_type()."""
    ets_rss_marker = RSSETSMarker(parcellation=PARCELLATION)
    input_ = "BOLD"
    output = ets_rss_marker.get_output_type(input_)
    assert output == "timeseries"


def test_store(tmp_path: Path) -> None:
    """Test RSS ETS store().

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with SPMAuditoryTestingDatagrabber() as dg:
        # Fetch element
        elem = dg["sub001"]
        # Load BOLD image
        niimg = image.load_img(str(elem["BOLD"]["path"].absolute()))
        elem["BOLD"]["data"] = niimg
        # Compute the RSSETSMarker
        ets_rss_marker = RSSETSMarker(parcellation=PARCELLATION)
        # Create storage
        storage = SQLiteFeatureStorage(
            uri=str((tmp_path / "test.sqlite").absolute())
        )
        # Store
        ets_rss_marker.fit_transform(input=elem, storage=storage)

        features = storage.list_features()
        assert any(x["name"] == "BOLD_RSSETSMarker" for x in features.values())
