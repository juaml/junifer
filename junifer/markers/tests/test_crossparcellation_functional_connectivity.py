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
            }
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


def test_store(tmp_path: Path) -> None:
    """Test CrossParcellationFC store().

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """

    with SPMAuditoryTestingDatagrabber() as dg:
        input_dict = dg["sub001"]
        niimg = image.load_img(str(input_dict["BOLD"]["path"].absolute()))

        input_dict["BOLD"]["data"] = niimg

        crossparcellation = CrossParcellationFC(
            parcellation_one=parcellation_ONE,
            parcellation_two=parcellation_TWO,
            correlation_method="spearman",
        )
        uri = tmp_path / "test_crossparcellation.sqlite"
        storage = SQLiteFeatureStorage(uri=uri, upsert="ignore")
        crossparcellation.fit_transform(input_dict, storage=storage)
        features = storage.list_features()
        assert any(
            x["name"] == "BOLD_CrossParcellationFC" for x in features.values()
        )


def test_get_output_type() -> None:
    """Test CrossParcellationFC get_output_type()."""

    crossparcellation = CrossParcellationFC(
        parcellation_one=parcellation_ONE, parcellation_two=parcellation_TWO
    )
    input_ = "BOLD"
    output = crossparcellation.get_output_type(input_)
    assert output == "matrix"


def test_init_() -> None:
    """Test CrossParcellationFC init()."""
    with pytest.raises(ValueError, match="must be different"):
        CrossParcellationFC(
            parcellation_one="a",
            parcellation_two="a",
            correlation_method="pearson",
        )
