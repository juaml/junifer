"""Provide tests for functional connectivity using maps."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from nilearn.connectome import ConnectivityMeasure
from nilearn.maskers import NiftiMapsMasker
from numpy.testing import assert_array_almost_equal
from sklearn.covariance import EmpiricalCovariance, LedoitWolf

from junifer.data import MapsRegistry
from junifer.datagrabber import PatternDataladDataGrabber
from junifer.datareader import DefaultDataReader
from junifer.markers import FunctionalConnectivityMaps
from junifer.storage import HDF5FeatureStorage


if TYPE_CHECKING:
    from sklearn.base import BaseEstimator


@pytest.mark.parametrize(
    "conn_method_params, cov_estimator",
    [
        ({"empirical": False}, LedoitWolf(store_precision=False)),
        ({"empirical": True}, EmpiricalCovariance(store_precision=False)),
    ],
)
def test_FunctionalConnectivityMaps(
    tmp_path: Path,
    maps_datagrabber: PatternDataladDataGrabber,
    conn_method_params: dict[str, bool],
    cov_estimator: type["BaseEstimator"],
) -> None:
    """Test FunctionalConnectivityParcels.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    maps_datagrabber : PatternDataladDataGrabber
        The testing PatternDataladDataGrabber, as fixture.
    conn_method_params : dict
        The parametrized parameters to connectivity measure method.
    cov_estimator : estimator object
        The parametrized covariance estimator.

    """
    with maps_datagrabber as dg:
        element = dg[("sub-01", "sub-001", "rest", "1")]
        element_data = DefaultDataReader().fit_transform(element)
        # Setup marker
        marker = FunctionalConnectivityMaps(
            maps="Smith_rsn_10",
            conn_method="correlation",
            conn_method_params=conn_method_params,
        )
        # Check correct output
        assert "matrix" == marker.get_output_type(
            input_type="BOLD", output_feature="functional_connectivity"
        )

        # Fit-transform the data
        fc = marker.fit_transform(element_data)
        fc_bold = fc["BOLD"]["functional_connectivity"]

        assert "data" in fc_bold
        assert "row_names" in fc_bold
        assert "col_names" in fc_bold
        assert fc_bold["data"].shape == (10, 10)
        assert len(set(fc_bold["row_names"])) == 10
        assert len(set(fc_bold["col_names"])) == 10

        # Compare with nilearn
        # Load testing maps for the target data
        maps, _ = MapsRegistry().get(
            maps="Smith_rsn_10",
            target_data=element_data["BOLD"],
        )
        # Extract timeseries
        masker = NiftiMapsMasker(maps_img=maps, standardize=False)
        extracted_timeseries = masker.fit_transform(
            element_data["BOLD"]["data"]
        )
        # Compute the connectivity measure
        connectivity_measure = ConnectivityMeasure(
            cov_estimator=cov_estimator,
            kind="correlation",  # type: ignore
        ).fit_transform([extracted_timeseries])[0]

        # Check that FC are almost equal
        assert_array_almost_equal(
            connectivity_measure, fc_bold["data"], decimal=3
        )

        # Store
        storage = HDF5FeatureStorage(
            uri=tmp_path / "test_fc_maps.hdf5",
        )
        marker.fit_transform(input=element_data, storage=storage)
        features = storage.list_features()
        assert any(
            x["name"]
            == "BOLD_FunctionalConnectivityMaps_functional_connectivity"
            for x in features.values()
        )
