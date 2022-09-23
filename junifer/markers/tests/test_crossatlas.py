"""Provide tests for marker class to calculate cross-atlas FC."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
#          Kaustubh R. Patil <k.patil@fz-juelich.de>
# License: AGPL

from nilearn import image

from junifer.markers.crossatlas import CrossAtlasFC
from junifer.testing.datagrabbers import SPMAuditoryTestingDatagrabber


def test_compute() -> None:
    """Test RSS ETS."""
    atlas_one = "Schaefer100x17"
    atlas_two = "Schaefer200x17"

    with SPMAuditoryTestingDatagrabber() as dg:
        out = dg["sub001"]
        niimg = image.load_img(str(out["BOLD"]["path"].absolute()))
        input_dict = {"data": niimg, "path": out["BOLD"]["path"]}

        crossatlas = CrossAtlasFC(
            atlas_one=atlas_one,
            atlas_two=atlas_two,
            correlation_method="spearman",
        )
        out = crossatlas.compute(input_dict)
        assert out["data"].shape == (200, 100)
        assert len(out["columns"]) == 100
        assert len(out["row_names"]) == 200
        meta = crossatlas.get_meta("BOLD")["marker"]
        assert meta["aggregation_method"] == "mean"
        assert meta["class"] == "CrossAtlasFC"
        assert meta["atlas_one"] == "Schaefer100x17"
        assert meta["atlas_two"] == "Schaefer200x17"
        assert meta["correlation_method"] == "spearman"


def test_get_output_kind() -> None:
    """Test get_output_kind."""

    atlas_one = "Schaefer100x17"
    atlas_two = "Schaefer200x17"
    ets_rss_marker = CrossAtlasFC(atlas_one=atlas_one, atlas_two=atlas_two)
    input_list = ["BOLD"]
    input_list = ets_rss_marker.get_output_kind(input_list)
    assert len(input_list) == 1
    assert input_list[0] in ["matrix"]
