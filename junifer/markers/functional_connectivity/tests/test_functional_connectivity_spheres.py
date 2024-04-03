"""Provide tests for functional connectivity spheres."""

# Authors: Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Kaustubh R. Patil <k.patil@fz-juelich.de>
#          Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

import pytest
from nilearn.connectome import ConnectivityMeasure
from nilearn.maskers import NiftiSpheresMasker
from numpy.testing import assert_array_almost_equal
from sklearn.covariance import EmpiricalCovariance

from junifer.data import get_coordinates
from junifer.datareader import DefaultDataReader
from junifer.markers.functional_connectivity import (
    FunctionalConnectivitySpheres,
)
from junifer.storage import SQLiteFeatureStorage
from junifer.testing.datagrabbers import SPMAuditoryTestingDataGrabber


def test_FunctionalConnectivitySpheres(tmp_path: Path) -> None:
    """Test FunctionalConnectivitySpheres.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with SPMAuditoryTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub001"])
        marker = FunctionalConnectivitySpheres(
            coords="DMNBuckner", radius=5.0, cor_method="correlation"
        )
        # Check correct output
        assert marker.get_output_type("BOLD") == "matrix"

        # Fit-transform the data
        fc = marker.fit_transform(element_data)
        fc_bold = fc["BOLD"]

        assert "data" in fc_bold
        assert "row_names" in fc_bold
        assert "col_names" in fc_bold
        assert fc_bold["data"].shape == (6, 6)
        assert len(set(fc_bold["row_names"])) == 6
        assert len(set(fc_bold["col_names"])) == 6

        # Compare with nilearn
        # Load testing coordinates for the target data
        testing_coords, _ = get_coordinates(
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
            kind="correlation"
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
            x["name"] == "BOLD_FunctionalConnectivitySpheres"
            for x in features.values()
        )


def test_FunctionalConnectivitySpheres_empirical(tmp_path: Path) -> None:
    """Test FunctionalConnectivitySpheres with empirical covariance.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with SPMAuditoryTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub001"])
        marker = FunctionalConnectivitySpheres(
            coords="DMNBuckner",
            radius=5.0,
            cor_method="correlation",
            cor_method_params={"empirical": True},
        )
        # Check correct output
        assert marker.get_output_type("BOLD") == "matrix"

        # Fit-transform the data
        fc = marker.fit_transform(element_data)
        fc_bold = fc["BOLD"]

        assert "data" in fc_bold
        assert "row_names" in fc_bold
        assert "col_names" in fc_bold
        assert fc_bold["data"].shape == (6, 6)
        assert len(set(fc_bold["row_names"])) == 6
        assert len(set(fc_bold["col_names"])) == 6

        # Compare with nilearn
        # Load testing coordinates for the target data
        testing_coords, _ = get_coordinates(
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
            cov_estimator=EmpiricalCovariance(), kind="correlation"  # type: ignore
        ).fit_transform([extracted_timeseries])[0]

        # Check that FC are almost equal
        assert_array_almost_equal(
            connectivity_measure, fc_bold["data"], decimal=3
        )


def test_FunctionalConnectivitySpheres_error() -> None:
    """Test FunctionalConnectivitySpheres errors."""
    with pytest.raises(ValueError, match="radius should be > 0"):
        FunctionalConnectivitySpheres(
            coords="DMNBuckner", radius=-0.1, cor_method="correlation"
        )
