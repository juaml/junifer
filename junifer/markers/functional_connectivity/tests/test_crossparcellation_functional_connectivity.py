"""Provide tests for marker class to calculate cross-parcellation FC."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
#          Kaustubh R. Patil <k.patil@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

import pytest

from junifer.datagrabber import DataType
from junifer.datareader import DefaultDataReader
from junifer.markers import CrossParcellationFC
from junifer.pipeline import WorkDirManager
from junifer.storage import SQLiteFeatureStorage, Upsert
from junifer.testing.datagrabbers import PartlyCloudyTestingDataGrabber


pytestmark = pytest.mark.external


parcellation_one = "Shen_2013_50"
parcellation_two = "Shen_2013_100"


def test_init() -> None:
    """Test CrossParcellationFC init()."""
    with pytest.raises(ValueError, match="must be different"):
        CrossParcellationFC(
            parcellation_one="a",
            parcellation_two="a",
            corr_method="pearson",
        )


def test_storage_type() -> None:
    """Test CrossParcellationFC storage_type."""
    assert "matrix" == CrossParcellationFC(
        parcellation_one=parcellation_one, parcellation_two=parcellation_two
    ).storage_type(
        input_type=DataType.BOLD, output_feature="functional_connectivity"
    )


def test_compute(tmp_path: Path) -> None:
    """Test CrossParcellationFC compute().

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with PartlyCloudyTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        WorkDirManager().workdir = tmp_path
        crossparcellation = CrossParcellationFC(
            parcellation_one=parcellation_one,
            parcellation_two=parcellation_two,
            corr_method="spearman",
        )
        out = crossparcellation.compute(element_data["BOLD"])[
            "functional_connectivity"
        ]
        assert out["data"].shape == (184, 93)
        assert len(out["col_names"]) == 93
        assert len(out["row_names"]) == 184


def test_store(tmp_path: Path) -> None:
    """Test CrossParcellationFC store().

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with PartlyCloudyTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        WorkDirManager().workdir = tmp_path
        crossparcellation = CrossParcellationFC(
            parcellation_one=parcellation_one,
            parcellation_two=parcellation_two,
            corr_method="spearman",
        )
        storage = SQLiteFeatureStorage(
            uri=tmp_path / "test_crossparcellation.sqlite",
            upsert=Upsert.Ignore,
        )
        # Fit transform marker on data with storage
        crossparcellation.fit_transform(input=element_data, storage=storage)
        features = storage.list_features()
        assert any(
            x["name"] == "BOLD_CrossParcellationFC_functional_connectivity"
            for x in features.values()
        )
