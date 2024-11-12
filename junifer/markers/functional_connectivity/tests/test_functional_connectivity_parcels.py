"""Provide tests for functional connectivity using parcellation."""

# Authors: Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Kaustubh R. Patil <k.patil@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from nilearn.connectome import ConnectivityMeasure
from nilearn.maskers import NiftiLabelsMasker
from numpy.testing import assert_array_almost_equal
from sklearn.covariance import EmpiricalCovariance, LedoitWolf

from junifer.data import ParcellationRegistry
from junifer.datareader import DefaultDataReader
from junifer.markers.functional_connectivity import (
    FunctionalConnectivityParcels,
)
from junifer.storage import SQLiteFeatureStorage
from junifer.testing.datagrabbers import PartlyCloudyTestingDataGrabber


if TYPE_CHECKING:
    from sklearn.base import BaseEstimator


@pytest.mark.parametrize(
    "conn_method_params, cov_estimator",
    [
        ({"empirical": False}, LedoitWolf(store_precision=False)),
        ({"empirical": True}, EmpiricalCovariance(store_precision=False)),
    ],
)
def test_FunctionalConnectivityParcels(
    tmp_path: Path,
    conn_method_params: dict[str, bool],
    cov_estimator: type["BaseEstimator"],
) -> None:
    """Test FunctionalConnectivityParcels.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    conn_method_params : dict
        The parametrized parameters to connectivity measure method.
    cov_estimator : estimator object
        The parametrized covariance estimator.

    """
    with PartlyCloudyTestingDataGrabber() as dg:
        # Get element data
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        # Setup marker
        marker = FunctionalConnectivityParcels(
            parcellation="TianxS1x3TxMNInonlinear2009cAsym",
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
        assert fc_bold["data"].shape == (16, 16)
        assert len(set(fc_bold["row_names"])) == 16
        assert len(set(fc_bold["col_names"])) == 16

        # Compare with nilearn
        # Load testing parcellation for the target data
        testing_parcellation, _ = ParcellationRegistry().get(
            parcellations=["TianxS1x3TxMNInonlinear2009cAsym"],
            target_data=element_data["BOLD"],
        )
        # Extract timeseries
        nifti_labels_masker = NiftiLabelsMasker(
            labels_img=testing_parcellation, standardize=False
        )
        extracted_timeseries = nifti_labels_masker.fit_transform(
            element_data["BOLD"]["data"]
        )
        # Compute the connectivity measure
        connectivity_measure = ConnectivityMeasure(
            cov_estimator=cov_estimator, kind="correlation"  # type: ignore
        ).fit_transform([extracted_timeseries])[0]

        # Check that FC are almost equal
        assert_array_almost_equal(
            connectivity_measure, fc_bold["data"], decimal=3
        )

        # Store
        storage = SQLiteFeatureStorage(
            uri=tmp_path / "test_fc_parcels.sqlite", upsert="ignore"
        )
        marker.fit_transform(input=element_data, storage=storage)
        features = storage.list_features()
        assert any(
            x["name"]
            == "BOLD_FunctionalConnectivityParcels_functional_connectivity"
            for x in features.values()
        )
