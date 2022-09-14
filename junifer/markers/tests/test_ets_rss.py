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
from junifer.testing.datagrabbers import SPMAuditoryTestingDatagrabber


def test_compute() -> None:
    """Test RSS ETS."""
    atlas = "Schaefer100x17"
    test_atlas, _, _ = load_atlas(atlas)

    with SPMAuditoryTestingDatagrabber() as dg:
        out = dg["sub001"]
        niimg = image.load_img(str(out["BOLD"]["path"].absolute()))
        input_dict = {"data": niimg, "path": out["BOLD"]["path"]}
        # Compute the RSSETSMarker
        ets_rss_marker = RSSETSMarker(atlas=atlas)
        new_out = ets_rss_marker.compute(input_dict)
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
    """Test get_output_kind."""

    atlas = "Schaefer100x17"
    ets_rss_marker = RSSETSMarker(atlas=atlas)
    input_list = ["BOLD"]
    input_list = ets_rss_marker.get_output_kind(input_list)
    assert len(input_list) == 1
    assert input_list[0] in ["timeseries"]


def test_store(tmp_path: Path) -> None:
    """Test store."""

    atlas = "Schaefer100x17"
    with SPMAuditoryTestingDatagrabber() as dg:
        out = dg["sub001"]
        niimg = image.load_img(str(out["BOLD"]["path"].absolute()))
        input_dict = {"data": niimg, "path": out["BOLD"]["path"]}
        # Compute the RSSETSMarker
        ets_rss_marker = RSSETSMarker(atlas=atlas)
        new_out = ets_rss_marker.compute(input_dict)
        storage = {
            "kind": "SQLiteFeatureStorage",
            "uri": str((tmp_path / "test.db").absolute()),
        }
        ets_rss_marker.store("SQLiteFeatureStorage", new_out, storage)
