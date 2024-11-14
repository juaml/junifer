"""Provide tests for functional connectivity spheres."""

# Authors: Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Kaustubh R. Patil <k.patil@fz-juelich.de>
#          Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from nilearn.connectome import ConnectivityMeasure
from nilearn.maskers import NiftiSpheresMasker
from numpy.testing import assert_array_almost_equal
from sklearn.covariance import EmpiricalCovariance, LedoitWolf

from junifer.data import CoordinatesRegistry
from junifer.datareader import DefaultDataReader
from junifer.markers.functional_connectivity import (
    FunctionalConnectivitySpheres,
)
from junifer.storage import SQLiteFeatureStorage
from junifer.testing.datagrabbers import SPMAuditoryTestingDataGrabber


if TYPE_CHECKING:
    from sklearn.base import BaseEstimator


@pytest.mark.parametrize(
    "conn_method_params, cov_estimator",
    [
        ({"empirical": False}, LedoitWolf(store_precision=False)),
        ({"empirical": True}, EmpiricalCovariance(store_precision=False)),
    ],
)
def test_FunctionalConnectivitySpheres(
    tmp_path: Path,
    conn_method_params: dict[str, bool],
    cov_estimator: type["BaseEstimator"],
) -> None:
    """Test FunctionalConnectivitySpheres.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    conn_method_params : dict
        The parametrized parameters to connectivity measure method.
    cov_estimator : estimator object
        The parametrized covariance estimator.

    """
    with SPMAuditoryTestingDataGrabber() as dg:
        # Get element data
        element_data = DefaultDataReader().fit_transform(dg["sub001"])
        # Setup marker
        marker = FunctionalConnectivitySpheres(
            coords="DMNBuckner",
            radius=5.0,
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
        assert fc_bold["data"].shape == (6, 6)
        assert len(set(fc_bold["row_names"])) == 6
        assert len(set(fc_bold["col_names"])) == 6

        # Compare with nilearn
        # Load testing coordinates for the target data
        testing_coords, _ = CoordinatesRegistry().get(
            coords="DMNBuckner", target_data=element_data["BOLD"]
        )
        # Extract timeseries
        nifti_spheres_masker = NiftiSpheresMasker(
            seeds=testing_coords, radius=5.0
        )
        extracted_timeseries = nifti_spheres_masker.fit_transform(
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
            uri=tmp_path / "test_fc_spheres.sqlite", upsert="ignore"
        )
        marker.fit_transform(input=element_data, storage=storage)
        features = storage.list_features()
        assert any(
            x["name"]
            == "BOLD_FunctionalConnectivitySpheres_functional_connectivity"
            for x in features.values()
        )


def test_FunctionalConnectivitySpheres_error() -> None:
    """Test FunctionalConnectivitySpheres errors."""
    with pytest.raises(ValueError, match="radius should be > 0"):
        FunctionalConnectivitySpheres(
            coords="DMNBuckner", radius=-0.1, conn_method="correlation"
        )
