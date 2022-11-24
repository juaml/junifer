"""Provide tests for ReHo on spheres."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

from nilearn import image as nimg

from junifer.markers.reho_spheres import ReHoSpheres
from junifer.storage.sqlite import SQLiteFeatureStorage
from junifer.testing.datagrabbers import SPMAuditoryTestingDatagrabber


COORDINATES = "DMNBuckner"


def test_reho_spheres_computation() -> None:
    """Test ReHoSpheres fit-transform."""
    with SPMAuditoryTestingDatagrabber() as dg:
        # Use first subject
        subject_data = dg["sub001"]
        # Load image to memory
        fmri_img = nimg.load_img(subject_data["BOLD"]["path"])
        # Initialize marker
        reho_spheres_marker = ReHoSpheres(coords=COORDINATES, radius=10.0)
        # Fit transform marker on data
        reho_spheres_output = reho_spheres_marker.fit_transform(
            {"BOLD": {"data": fmri_img}}
        )
        # Get BOLD output
        reho_spheres_output_bold = reho_spheres_output["BOLD"]
        # Assert BOLD output
        assert "data" in reho_spheres_output_bold
        assert "columns" in reho_spheres_output_bold
        assert "rows_col_name" in reho_spheres_output_bold
        # TODO: add comparison with afni 3dReHo generated data


def test_reho_spheres_storage(tmp_path: Path) -> None:
    """Test ReHoSpheres storage.

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
        reho_spheres_marker = ReHoSpheres(coords=COORDINATES, radius=10.0)
        # Initialize storage
        reho_spheres_storage = SQLiteFeatureStorage(
            tmp_path / "reho_spheres.sqlite"
        )
        # Generate meta
        meta = {"element": "sub001"}  # only requires element key for storing
        # Fit transform marker on data with storage
        reho_spheres_marker.fit_transform(
            input={"BOLD": {"data": fmri_img}, "meta": meta},
            storage=reho_spheres_storage,
        )
