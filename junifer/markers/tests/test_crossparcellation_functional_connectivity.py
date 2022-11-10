"""Provide tests for marker class to calculate cross-parcellation FC."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
#          Kaustubh R. Patil <k.patil@fz-juelich.de>
# License: AGPL

from pathlib import Path

import pytest
from nilearn import image

from junifer.markers.crossparcellation_functional_connectivity import (
    CrossParcellationFC,
)
from junifer.storage import SQLiteFeatureStorage
from junifer.testing.datagrabbers import SPMAuditoryTestingDatagrabber

parcellation_ONE = "Schaefer100x17"
parcellation_TWO = "Schaefer200x17"


def test_compute() -> None:
    """Test CrossParcellationFC compute()."""

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

        crossparcellation = CrossParcellationFC(
            parcellation_one=parcellation_ONE,
            parcellation_two=parcellation_TWO,
            correlation_method="spearman",
        )
        out = crossparcellation.compute(input_dict["BOLD"])
        assert out["data"].shape == (200, 100)
        assert len(out["col_names"]) == 100
        assert len(out["row_names"]) == 200
        meta = crossparcellation.get_meta("BOLD")["marker"]
        assert meta["aggregation_method"] == "mean"
        assert meta["class"] == "CrossParcellationFC"
        assert meta["parcellation_one"] == "Schaefer100x17"
        assert meta["parcellation_two"] == "Schaefer200x17"
        assert meta["correlation_method"] == "spearman"


def test_store(tmp_path: Path) -> None:
    """Test CrossParcellationFC store().

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

        crossparcellation = CrossParcellationFC(
            parcellation_one=parcellation_ONE,
            parcellation_two=parcellation_TWO,
            correlation_method="spearman",
        )
        uri = tmp_path / "test_crossparcellation.db"
        storage = SQLiteFeatureStorage(
            uri=uri, single_output=True, upsert="ignore"
        )
        out = crossparcellation.fit_transform(input_dict, storage=storage)


def test_get_output_kind() -> None:
    """Test CrossParcellationFC get_output_kind()."""

    crossparcellation = CrossParcellationFC(
        parcellation_one=parcellation_ONE, parcellation_two=parcellation_TWO
    )
    input_list = ["BOLD"]
    input_list = crossparcellation.get_output_kind(input_list)
    assert len(input_list) == 1
    assert input_list[0] in ["matrix"]


def test_init_() -> None:
    """Test CrossParcellationFC init()."""
    with pytest.raises(ValueError, match="must be different"):
        CrossParcellationFC(
            parcellation_one="a",
            parcellation_two="a",
            correlation_method="pearson",
        )
