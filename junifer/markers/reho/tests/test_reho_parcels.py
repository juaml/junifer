"""Provide tests for ReHo on parcels."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

from nilearn import image as nimg

from junifer.markers.reho.reho_parcels import ReHoParcels
from junifer.storage.sqlite import SQLiteFeatureStorage
from junifer.testing.datagrabbers import SPMAuditoryTestingDatagrabber


PARCELLATION = "Schaefer100x7"


def test_reho_parcels_computation() -> None:
    """Test ReHoParcels fit-transform."""
    with SPMAuditoryTestingDatagrabber() as dg:
        # Use first subject
        subject_data = dg["sub001"]
        # Load image to memory
        fmri_img = nimg.load_img(subject_data["BOLD"]["path"])
        # Initialize marker
        reho_parcels_marker = ReHoParcels(parcellation=PARCELLATION)
        # Fit transform marker on data
        reho_parcels_output = reho_parcels_marker.fit_transform(
            {"BOLD": {"data": fmri_img}}
        )
        # Get BOLD output
        reho_parcels_output_bold = reho_parcels_output["BOLD"]
        # Assert BOLD output
        assert "data" in reho_parcels_output_bold
        assert "columns" in reho_parcels_output_bold
        assert "rows_col_name" in reho_parcels_output_bold
        # TODO: add comparison with afni 3dReHo generated data


def test_reho_parcels_storage(tmp_path: Path) -> None:
    """Test ReHoParcels storage.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with SPMAuditoryTestingDatagrabber() as dg:
        # Use first subject
        subject_data = dg["sub001"]
        # Load image to memory
        fmri_img = nimg.load_img(subject_data["BOLD"]["path"])
        # Initialize marker
        reho_parcels_marker = ReHoParcels(parcellation=PARCELLATION)
        # Initialize storage
        reho_parcels_storage = SQLiteFeatureStorage(
            tmp_path / "reho_parcels.sqlite"
        )
        # Generate meta
        meta = {"element": "sub001"}  # only requires element key for storing
        # Fit transform marker on data with storage
        reho_parcels_marker.fit_transform(
            input={"BOLD": {"data": fmri_img}, "meta": meta},
            storage=reho_parcels_storage,
        )
