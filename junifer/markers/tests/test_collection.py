"""Provide tests for marker collection."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

import pytest
from numpy.testing import assert_array_equal

from junifer.datareader.default import DefaultDataReader
from junifer.markers import (
    FunctionalConnectivityParcels,
    MarkerCollection,
    ParcelAggregation,
)
from junifer.pipeline import PipelineStepMixin
from junifer.preprocess import fMRIPrepConfoundRemover
from junifer.storage import SQLiteFeatureStorage
from junifer.testing.datagrabbers import (
    OasisVBMTestingDatagrabber,
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
        MarkerCollection(wrong_markers)


def test_marker_collection() -> None:
    """Test MarkerCollection."""
    markers = [
        ParcelAggregation(
            parcellation="Schaefer100x7",
            method="mean",
            name="gmd_schaefer100x7_mean",
        ),
        ParcelAggregation(
            parcellation="Schaefer100x7",
            method="std",
            name="gmd_schaefer100x7_std",
        ),
        ParcelAggregation(
            parcellation="Schaefer100x7",
            method="trim_mean",
            method_params={"proportiontocut": 0.1},
            name="gmd_schaefer100x7_trim_mean90",
        ),
    ]
    mc = MarkerCollection(markers=markers)
    assert mc._markers == markers
    assert mc._preprocessing is None
    assert mc._storage is None
    assert isinstance(mc._datareader, DefaultDataReader)

    # Create testing datagrabber
    dg = OasisVBMTestingDatagrabber()
    mc.validate(dg)

    with dg:
        input = dg["sub-01"]
        out = mc.fit(input)
        assert out is not None
        assert isinstance(out, dict)
        assert len(out) == 3
        assert "gmd_schaefer100x7_mean" in out
        assert "gmd_schaefer100x7_std" in out
        assert "gmd_schaefer100x7_trim_mean90" in out

        for t_marker in markers:
            t_name = t_marker.name
            assert "VBM_GM" in out[t_name]
            t_vbm = out[t_name]["VBM_GM"]
            assert "data" in t_vbm
            assert "columns" in t_vbm
            assert "meta" in t_vbm

    # Test preprocessing
    class BypassPreprocessing(PipelineStepMixin):
        def fit_transform(self, input):
            return input

    mc2 = MarkerCollection(
        markers=markers,
        preprocessing=BypassPreprocessing(),
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
                out[t_name]["VBM_GM"]["data"], out2[t_name]["VBM_GM"]["data"]
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
        markers=markers,
        preprocessing=fMRIPrepConfoundRemover(),
    )
    assert mc._markers == markers
    assert mc._preprocessing is not None
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
            parcellation="Schaefer100x7",
            method="mean",
            name="gmd_schaefer100x7_mean",
        ),
        ParcelAggregation(
            parcellation="Schaefer100x7",
            method="std",
            name="gmd_schaefer100x7_std",
        ),
        ParcelAggregation(
            parcellation="Schaefer100x7",
            method="trim_mean",
            method_params={"proportiontocut": 0.1},
            name="gmd_schaefer100x7_trim_mean90",
        ),
    ]
    # Test storage
    dg = OasisVBMTestingDatagrabber()

    uri = tmp_path / "test_marker_collection_storage.sqlite"
    storage = SQLiteFeatureStorage(uri=uri)
    mc = MarkerCollection(
        markers=markers,
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

    mc2 = MarkerCollection(markers=markers, datareader=DefaultDataReader())
    mc2.validate(dg)
    assert mc2._storage is None

    with dg:
        input = dg["sub-01"]
        out = mc2.fit(input)

    features = storage.list_features()
    assert len(features) == 3
    feature_md5 = list(features.keys())[0]
    t_feature = storage.read_df(feature_md5=feature_md5)
    fname = "gmd_schaefer100x7_mean"
    t_data = out[fname]["VBM_GM"]["data"]  # type: ignore
    cols = out[fname]["VBM_GM"]["columns"]  # type: ignore
    assert_array_equal(t_feature[cols].values, t_data)  # type: ignore

    feature_md5 = list(features.keys())[1]
    t_feature = storage.read_df(feature_md5=feature_md5)
    fname = "gmd_schaefer100x7_std"
    t_data = out[fname]["VBM_GM"]["data"]  # type: ignore
    cols = out[fname]["VBM_GM"]["columns"]  # type: ignore
    assert_array_equal(t_feature[cols].values, t_data)  # type: ignore

    feature_md5 = list(features.keys())[2]
    t_feature = storage.read_df(feature_md5=feature_md5)
    fname = "gmd_schaefer100x7_trim_mean90"
    t_data = out[fname]["VBM_GM"]["data"]  # type: ignore
    cols = out[fname]["VBM_GM"]["columns"]  # type: ignore
    assert_array_equal(t_feature[cols].values, t_data)  # type: ignore
