"""Provide tests for MarkerCollection."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

import pytest
from numpy.testing import assert_array_equal

from junifer.datareader.default import DefaultDataReader
from junifer.markers import (
    FunctionalConnectivityParcels,
    ParcelAggregation,
)
from junifer.pipeline import MarkerCollection, PipelineStepMixin
from junifer.preprocess import fMRIPrepConfoundRemover
from junifer.storage import SQLiteFeatureStorage
from junifer.testing.datagrabbers import (
    PartlyCloudyTestingDataGrabber,
)


def test_marker_collection_incorrect_markers() -> None:
    """Test incorrect markers for MarkerCollection."""
    wrong_markers = [
        ParcelAggregation(
            parcellation="Schaefer100x7",
            method="mean",
            name="gmd_schaefer100x7_mean",
        ),
        ParcelAggregation(
            parcellation="Schaefer100x7",
            method="mean",
            name="gmd_schaefer100x7_mean",
        ),
    ]
    with pytest.raises(ValueError, match=r"must have different names"):
        MarkerCollection(wrong_markers)  # type: ignore


def test_marker_collection() -> None:
    """Test MarkerCollection."""
    markers = [
        ParcelAggregation(
            parcellation="TianxS2x3TxMNInonlinear2009cAsym",
            method="mean",
            name="tian_mean",
        ),
        ParcelAggregation(
            parcellation="TianxS2x3TxMNInonlinear2009cAsym",
            method="std",
            name="tian_std",
        ),
        ParcelAggregation(
            parcellation="TianxS2x3TxMNInonlinear2009cAsym",
            method="trim_mean",
            method_params={"proportiontocut": 0.1},
            name="tian_trim_mean90",
        ),
    ]
    mc = MarkerCollection(markers=markers)  # type: ignore
    assert mc._markers == markers
    assert mc._preprocessors is None
    assert mc._storage is None
    assert isinstance(mc._datareader, DefaultDataReader)

    # Create testing datagrabber
    dg = PartlyCloudyTestingDataGrabber()
    mc.validate(dg)

    with dg:
        input = dg["sub-01"]
        out = mc.fit(input)
        assert out is not None
        assert isinstance(out, dict)
        assert len(out) == 3
        assert "tian_mean" in out
        assert "tian_std" in out
        assert "tian_trim_mean90" in out

        for t_marker in markers:
            t_name = t_marker.name
            assert "BOLD" in out[t_name]
            t_bold = out[t_name]["BOLD"]["aggregation"]
            assert "data" in t_bold
            assert "col_names" in t_bold
            assert "meta" in t_bold

    # Test preprocessing
    class BypassPreprocessing(PipelineStepMixin):
        def fit_transform(self, input):
            return input

    mc2 = MarkerCollection(
        markers=markers,  # type: ignore
        preprocessors=[BypassPreprocessing()],  # type: ignore
        datareader=DefaultDataReader(),
    )
    assert isinstance(mc2._datareader, DefaultDataReader)
    with dg:
        input = dg["sub-01"]
        out2 = mc2.fit(input)
        assert out2 is not None
        for t_marker in markers:
            t_name = t_marker.name
            assert_array_equal(
                out[t_name]["BOLD"]["aggregation"]["data"],
                out2[t_name]["BOLD"]["aggregation"]["data"],
            )


def test_marker_collection_with_preprocessing() -> None:
    """Test MarkerCollection with preprocessing."""
    markers = [
        FunctionalConnectivityParcels(
            parcellation="Schaefer100x17",
            agg_method="mean",
            name="Schaefer100x17_mean_FC",
        ),
        FunctionalConnectivityParcels(
            parcellation="TianxS2x3TxMNInonlinear2009cAsym",
            agg_method="mean",
            name="TianxS2x3TxMNInonlinear2009cAsym_mean_FC",
        ),
    ]
    mc = MarkerCollection(
        markers=markers,  # type: ignore
        preprocessors=[fMRIPrepConfoundRemover()],
    )
    assert mc._markers == markers
    assert mc._preprocessors is not None
    assert mc._storage is None
    assert isinstance(mc._datareader, DefaultDataReader)

    # Create testing datagrabber
    dg = PartlyCloudyTestingDataGrabber(reduce_confounds=False)
    mc.validate(dg)


def test_marker_collection_storage(tmp_path: Path) -> None:
    """Test marker collection with storage.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    markers = [
        ParcelAggregation(
            parcellation="TianxS2x3TxMNInonlinear2009cAsym",
            method="mean",
            name="tian_mean",
        ),
        ParcelAggregation(
            parcellation="TianxS2x3TxMNInonlinear2009cAsym",
            method="std",
            name="tian_std",
        ),
        ParcelAggregation(
            parcellation="TianxS2x3TxMNInonlinear2009cAsym",
            method="trim_mean",
            method_params={"proportiontocut": 0.1},
            name="tian_trim_mean90",
        ),
    ]
    # Setup datagrabber
    dg = PartlyCloudyTestingDataGrabber()
    # Setup storage
    storage = SQLiteFeatureStorage(
        tmp_path / "test_marker_collection_storage.sqlite"
    )
    mc = MarkerCollection(
        markers=markers,  # type: ignore
        storage=storage,
        datareader=DefaultDataReader(),
    )
    mc.validate(dg)
    assert mc._storage is not None
    assert mc._storage.uri == storage.uri
    with dg:
        input = dg["sub-01"]
        out = mc.fit(input)
        assert out is None

    mc2 = MarkerCollection(
        markers=markers, datareader=DefaultDataReader()  # type: ignore
    )
    mc2.validate(dg)
    assert mc2._storage is None

    with dg:
        input = dg["sub-01"]
        out = mc2.fit(input)

    features = storage.list_features()
    assert len(features) == 3

    feature_md5 = next(iter(features.keys()))
    t_feature = storage.read_df(feature_md5=feature_md5)
    fname = "tian_mean"
    t_data = out[fname]["BOLD"]["aggregation"]["data"]  # type: ignore
    cols = out[fname]["BOLD"]["aggregation"]["col_names"]  # type: ignore
    assert_array_equal(t_feature[cols].values, t_data)  # type: ignore

    feature_md5 = list(features.keys())[1]
    t_feature = storage.read_df(feature_md5=feature_md5)
    fname = "tian_std"
    t_data = out[fname]["BOLD"]["aggregation"]["data"]  # type: ignore
    cols = out[fname]["BOLD"]["aggregation"]["col_names"]  # type: ignore
    assert_array_equal(t_feature[cols].values, t_data)  # type: ignore

    feature_md5 = list(features.keys())[2]
    t_feature = storage.read_df(feature_md5=feature_md5)
    fname = "tian_trim_mean90"
    t_data = out[fname]["BOLD"]["aggregation"]["data"]  # type: ignore
    cols = out[fname]["BOLD"]["aggregation"]["col_names"]  # type: ignore
    assert_array_equal(t_feature[cols].values, t_data)  # type: ignore
