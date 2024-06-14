"""Provide tests for marker class to calculate cross-parcellation FC."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
#          Kaustubh R. Patil <k.patil@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

import pytest

from junifer.datareader import DefaultDataReader
from junifer.markers.functional_connectivity import CrossParcellationFC
from junifer.pipeline import WorkDirManager
from junifer.pipeline.utils import _check_ants
from junifer.storage import SQLiteFeatureStorage
from junifer.testing.datagrabbers import SPMAuditoryTestingDataGrabber


parcellation_one = "Schaefer100x17"
parcellation_two = "Schaefer200x17"


def test_init() -> None:
    """Test CrossParcellationFC init()."""
    with pytest.raises(ValueError, match="must be different"):
        CrossParcellationFC(
            parcellation_one="a",
            parcellation_two="a",
            corr_method="pearson",
        )


def test_get_output_type() -> None:
    """Test CrossParcellationFC get_output_type()."""
    assert "matrix" == CrossParcellationFC(
        parcellation_one=parcellation_one, parcellation_two=parcellation_two
    ).get_output_type(
        input_type="BOLD", output_feature="functional_connectivity"
    )


@pytest.mark.skipif(
    _check_ants() is False, reason="requires ANTs to be in PATH"
)
def test_compute(tmp_path: Path) -> None:
    """Test CrossParcellationFC compute().

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with SPMAuditoryTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub001"])
        WorkDirManager().workdir = tmp_path
        crossparcellation = CrossParcellationFC(
            parcellation_one=parcellation_one,
            parcellation_two=parcellation_two,
            corr_method="spearman",
        )
        out = crossparcellation.compute(element_data["BOLD"])[
            "functional_connectivity"
        ]
        assert out["data"].shape == (200, 100)
        assert len(out["col_names"]) == 100
        assert len(out["row_names"]) == 200


@pytest.mark.skipif(
    _check_ants() is False, reason="requires ANTs to be in PATH"
)
def test_store(tmp_path: Path) -> None:
    """Test CrossParcellationFC store().

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with SPMAuditoryTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub001"])
        WorkDirManager().workdir = tmp_path
        crossparcellation = CrossParcellationFC(
            parcellation_one=parcellation_one,
            parcellation_two=parcellation_two,
            corr_method="spearman",
        )
        storage = SQLiteFeatureStorage(
            uri=tmp_path / "test_crossparcellation.sqlite", upsert="ignore"
        )
        # Fit transform marker on data with storage
        crossparcellation.fit_transform(input=element_data, storage=storage)
        features = storage.list_features()
        assert any(
            x["name"] == "BOLD_CrossParcellationFC_functional_connectivity"
            for x in features.values()
        )
