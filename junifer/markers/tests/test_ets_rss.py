"""Provide test for root sum of squares of edgewise timeseries."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
#          Nicolás Nieto <n.nieto@fz-juelich.de>
#          Sami Hamdan <s.hamdan@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

from nilearn import image
from nilearn.maskers import NiftiLabelsMasker

from junifer.data import load_atlas
from junifer.markers.ets_rss import RSSETSMarker
from junifer.storage import SQLiteFeatureStorage
from junifer.testing.datagrabbers import SPMAuditoryTestingDatagrabber


# Set atlas
ATLAS = "Schaefer100x17"


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
        ets_rss_marker = RSSETSMarker(atlas=ATLAS)
        new_out = ets_rss_marker.compute(input_dict)

        # Load atlas
        test_atlas, _, _ = load_atlas(ATLAS)
        # Compute the NiftiLabelsMasker
        test_masker = NiftiLabelsMasker(test_atlas)
        test_ts = test_masker.fit_transform(niimg)
        # Assert the dimension of timeseries
        n_time, _ = test_ts.shape
        assert n_time == len(new_out["data"])

        # Assert the meta
        meta = ets_rss_marker.get_meta("BOLD")["marker"]
        assert meta["atlas"] == "Schaefer100x17"
        assert meta["aggregation_method"] == "mean"
        assert meta["class"] == "RSSETSMarker"


def test_get_output_kind() -> None:
    """Test RSS ETS get_output_kind()."""
    ets_rss_marker = RSSETSMarker(atlas=ATLAS)
    input_list = ["BOLD"]
    input_list = ets_rss_marker.get_output_kind(input_list)
    assert len(input_list) == 1
    assert input_list[0] in ["timeseries"]


def test_store(tmp_path: Path) -> None:
    """Test RSS ETS store().

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with SPMAuditoryTestingDatagrabber() as dg:
        # Fetch element
        out = dg["sub001"]
        # Load BOLD image
        niimg = image.load_img(str(out["BOLD"]["path"].absolute()))
        input_dict = {"data": niimg, "path": out["BOLD"]["path"]}
        # Compute the RSSETSMarker
        ets_rss_marker = RSSETSMarker(atlas=ATLAS)
        # Create storage
        storage = SQLiteFeatureStorage(
            uri=str((tmp_path / "test.db").absolute()),
            single_output=True,
        )
        # Store
        ets_rss_marker.fit_transform(input=input_dict, storage=storage)
