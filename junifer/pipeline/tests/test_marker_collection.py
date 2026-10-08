"""Provide tests for MarkerCollection."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

import numpy as np
import pytest
from numpy.testing import assert_array_equal

from junifer.datagrabber import DataType
from junifer.datareader import DefaultDataReader
from junifer.markers import FunctionalConnectivityParcels, ParcelAggregation
from junifer.markers.base import BaseMarker
from junifer.pipeline import MarkerCollection, PipelineStepMixin
from junifer.preprocess import fMRIPrepConfoundRemover
from junifer.storage import SQLiteFeatureStorage, StorageType
from junifer.testing.datagrabbers import PartlyCloudyTestingDataGrabber


pytestmark = pytest.mark.external

PARCELLATION = "TianxS2x3TxMNInonlinear2009cAsym"


def _markers() -> list[ParcelAggregation]:
    """Get markers aggregating the BOLD data in different ways.

    Returns
    -------
    list of ParcelAggregation
        The markers, named ``tian_mean``, ``tian_std`` and
        ``tian_trim_mean90``.

    """
    return [
        ParcelAggregation(
            parcellation=PARCELLATION, method="mean", name="tian_mean"
        ),
        ParcelAggregation(
            parcellation=PARCELLATION, method="std", name="tian_std"
        ),
        ParcelAggregation(
            parcellation=PARCELLATION,
            method="trim_mean",
            method_params={"proportiontocut": 0.1},
            name="tian_trim_mean90",
        ),
    ]


def _fit(mc: MarkerCollection) -> dict | None:
    """Validate and fit a marker collection on one subject.

    Parameters
    ----------
    mc : MarkerCollection
        The marker collection.

    Returns
    -------
    dict or None
        The output of the marker collection.

    """
    dg = PartlyCloudyTestingDataGrabber(n_timepoints=50)
    mc.validate(dg)
    with dg:
        return mc.fit(dg["sub-01"])


def test_marker_collection_same_names() -> None:
    """Test markers must have different names."""
    markers = [
        ParcelAggregation(parcellation=PARCELLATION, method="mean", name="a"),
        ParcelAggregation(parcellation=PARCELLATION, method="std", name="a"),
    ]
    with pytest.raises(ValueError, match=r"must have different names"):
        MarkerCollection(markers=markers)  # type: ignore


def test_marker_collection_defaults() -> None:
    """Test the defaults of MarkerCollection."""
    markers = _markers()
    mc = MarkerCollection(markers=markers)  # type: ignore
    assert mc._markers == markers
    assert mc._preprocessors is None
    assert mc._storage is None
    assert isinstance(mc._datareader, DefaultDataReader)


def test_marker_collection_fit() -> None:
    """Test MarkerCollection returns the output of each marker."""
    out = _fit(MarkerCollection(markers=_markers()))  # type: ignore
    assert out is not None
    assert set(out) == {"tian_mean", "tian_std", "tian_trim_mean90"}
    for name in out:
        aggregation = out[name]["BOLD"]["aggregation"]
        assert {"data", "col_names", "meta"} <= set(aggregation)


def test_marker_collection_preprocessing() -> None:
    """Test MarkerCollection computes the markers on the preprocessed data."""

    class Unchanged(PipelineStepMixin):
        """Preprocessing that returns the data unchanged."""

        def validate_input(self, input):
            return input

        def fit_transform(self, input):
            return input

    out = _fit(MarkerCollection(markers=_markers()))  # type: ignore
    out_preprocessed = _fit(
        MarkerCollection(
            markers=_markers(),  # type: ignore
            preprocessors=[Unchanged()],  # type: ignore
        )
    )
    assert out is not None
    assert out_preprocessed is not None
    for name in out:
        assert_array_equal(
            out[name]["BOLD"]["aggregation"]["data"],
            out_preprocessed[name]["BOLD"]["aggregation"]["data"],
        )


def test_marker_collection_validate_preprocessing() -> None:
    """Test MarkerCollection validates with a confound removal step."""
    mc = MarkerCollection(
        markers=[  # type: ignore
            FunctionalConnectivityParcels(
                parcellation=PARCELLATION, agg_method="mean", name="tian_fc"
            ),
        ],
        preprocessors=[fMRIPrepConfoundRemover()],
    )
    assert mc._preprocessors is not None
    mc.validate(PartlyCloudyTestingDataGrabber(reduce_confounds=False))


def test_marker_collection_storage(tmp_path: Path) -> None:
    """Test MarkerCollection stores the output of each marker.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    storage = SQLiteFeatureStorage(uri=tmp_path / "features.sqlite")
    mc = MarkerCollection(markers=_markers(), storage=storage)  # type: ignore
    assert mc._storage is storage
    # Nothing is returned when storing
    assert _fit(mc) is None

    # The stored features are the same as the ones returned without storage
    out = _fit(MarkerCollection(markers=_markers()))  # type: ignore
    assert out is not None
    features = storage.list_features()
    assert len(features) == len(out)
    for md5, feature in features.items():
        # Features are named "<type>_<marker>_<feature>"
        name = feature["name"].removeprefix("BOLD_")
        name = name.removesuffix("_aggregation")
        aggregation = out[name]["BOLD"]["aggregation"]
        stored = storage.read_df(feature_md5=md5)
        assert_array_equal(
            stored[aggregation["col_names"]].to_numpy(), aggregation["data"]
        )


def test_marker_collection_marker_changes_data() -> None:
    """Test markers cannot change the data shared with the other markers."""

    class ChangingMarker(BaseMarker):
        """Marker that replaces the BOLD data."""

        _MARKER_INOUT_MAPPINGS = {  # noqa: RUF012
            DataType.BOLD: {"feat": StorageType.Vector},
        }

        def compute(self, input, extra_input=None):
            input["data"] = "changed"
            return {"feat": {"data": np.zeros((1, 1)), "col_names": ["x"]}}

    mc = MarkerCollection(
        markers=[ChangingMarker(name="changing"), *_markers()]  # type: ignore
    )
    with pytest.raises(RuntimeError, match=r"changing changed .*BOLD.data"):
        _fit(mc)
