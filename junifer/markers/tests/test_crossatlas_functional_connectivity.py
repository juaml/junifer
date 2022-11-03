"""Provide tests for marker class to calculate cross-atlas FC."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
#          Kaustubh R. Patil <k.patil@fz-juelich.de>
# License: AGPL

from pathlib import Path

from nilearn import image

from junifer.markers.crossatlas_functional_connectivity import CrossAtlasFC
from junifer.storage import SQLiteFeatureStorage
from junifer.testing.datagrabbers import SPMAuditoryTestingDatagrabber


ATLAS_ONE = "Schaefer100x17"
ATLAS_TWO = "Schaefer200x17"


def test_compute() -> None:
    """Test CrossAtlasFC compute()."""

    with SPMAuditoryTestingDatagrabber() as dg:
        out = dg["sub001"]
        niimg = image.load_img(str(out["BOLD"]["path"].absolute()))
        input_dict = {
            "BOLD": {
                "data": niimg,
                "path": out["BOLD"]["path"],
                "meta": {"element": "sub001"},
            },
            "meta": {"element": "sub001"},
        }

        crossatlas = CrossAtlasFC(
            atlas_one=ATLAS_ONE,
            atlas_two=ATLAS_TWO,
            correlation_method="spearman",
        )
        out = crossatlas.compute(input_dict["BOLD"])
        assert out["data"].shape == (200, 100)
        assert len(out["col_names"]) == 100
        assert len(out["row_names"]) == 200
        meta = crossatlas.get_meta("BOLD")["marker"]
        assert meta["aggregation_method"] == "mean"
        assert meta["class"] == "CrossAtlasFC"
        assert meta["atlas_one"] == "Schaefer100x17"
        assert meta["atlas_two"] == "Schaefer200x17"
        assert meta["correlation_method"] == "spearman"


def test_store(tmp_path: Path) -> None:
    """Test CrossAtlasFC store().

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """

    with SPMAuditoryTestingDatagrabber() as dg:
        out = dg["sub001"]
        niimg = image.load_img(str(out["BOLD"]["path"].absolute()))
        input_dict = {
            "BOLD": {
                "data": niimg,
                "path": out["BOLD"]["path"],
                "meta": {"element": "sub001"},
            },
            "meta": {"element": "sub001"},
        }

        crossatlas = CrossAtlasFC(
            atlas_one=ATLAS_ONE,
            atlas_two=ATLAS_TWO,
            correlation_method="spearman",
        )
        uri = tmp_path / "test_crossatlas.db"
        storage = SQLiteFeatureStorage(
            uri=uri, single_output=True, upsert="ignore"
        )
        out = crossatlas.fit_transform(input_dict, storage=storage)


def test_get_output_kind() -> None:
    """Test CrossAtlasFC get_output_kind()."""

    crossatlas = CrossAtlasFC(atlas_one=ATLAS_ONE, atlas_two=ATLAS_TWO)
    input_list = ["BOLD"]
    input_list = crossatlas.get_output_kind(input_list)
    assert len(input_list) == 1
    assert input_list[0] in ["matrix"]
