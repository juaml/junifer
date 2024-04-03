"""Provide tests for functional connectivity using parcellation."""

# Authors: Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Kaustubh R. Patil <k.patil@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

from nilearn.connectome import ConnectivityMeasure
from nilearn.maskers import NiftiLabelsMasker
from numpy.testing import assert_array_almost_equal

from junifer.data import get_parcellation
from junifer.datareader import DefaultDataReader
from junifer.markers.functional_connectivity import (
    FunctionalConnectivityParcels,
)
from junifer.storage import SQLiteFeatureStorage
from junifer.testing.datagrabbers import PartlyCloudyTestingDataGrabber


def test_FunctionalConnectivityParcels(tmp_path: Path) -> None:
    """Test FunctionalConnectivityParcels.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with PartlyCloudyTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        marker = FunctionalConnectivityParcels(
            parcellation="TianxS1x3TxMNInonlinear2009cAsym"
        )
        # Check correct output
        assert marker.get_output_type("BOLD") == "matrix"

        # Fit-transform the data
        fc = marker.fit_transform(element_data)
        fc_bold = fc["BOLD"]

        assert "data" in fc_bold
        assert "row_names" in fc_bold
        assert "col_names" in fc_bold
        assert fc_bold["data"].shape == (16, 16)
        assert len(set(fc_bold["row_names"])) == 16
        assert len(set(fc_bold["col_names"])) == 16

        # Compare with nilearn
        # Load testing parcellation for the target data
        testing_parcellation, _ = get_parcellation(
            parcellation=["TianxS1x3TxMNInonlinear2009cAsym"],
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
            kind="covariance"
        ).fit_transform([extracted_timeseries])[0]

        # Check that FC are almost equal
        assert_array_almost_equal(
            connectivity_measure, fc_bold["data"], decimal=3
        )

        # Check empirical correlation method parameters
        marker = FunctionalConnectivityParcels(
            parcellation="TianxS1x3TxMNInonlinear2009cAsym",
            cor_method_params={"empirical": True},
        )
        # Store
        storage = SQLiteFeatureStorage(
            uri=tmp_path / "test_fc_parcels.sqlite", upsert="ignore"
        )
        marker.fit_transform(input=element_data, storage=storage)
        features = storage.list_features()
        assert any(
            x["name"] == "BOLD_FunctionalConnectivityParcels"
            for x in features.values()
        )
