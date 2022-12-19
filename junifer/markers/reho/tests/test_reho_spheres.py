"""Provide tests for ReHo on spheres."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

import pytest
from nilearn import image as nimg
from scipy.stats import pearsonr

from junifer.markers.reho.reho_spheres import ReHoSpheres
from junifer.pipeline.utils import _check_afni
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
            {"BOLD": {"path": "/tmp", "data": fmri_img, "meta": {}}}
        )
        # Get BOLD output
        reho_spheres_output_bold = reho_spheres_output["BOLD"]
        # Assert BOLD output keys
        assert "data" in reho_spheres_output_bold
        assert "columns" in reho_spheres_output_bold

        reho_spheres_output_bold_data = reho_spheres_output_bold["data"]
        # Assert BOLD output data dimension
        assert reho_spheres_output_bold_data.ndim == 2
        # Assert BOLD output data is normalized
        assert (reho_spheres_output_bold_data > 0).all() and (
            reho_spheres_output_bold_data < 1
        ).all()


@pytest.mark.skipif(
    _check_afni() is False, reason="requires afni to be in PATH"
)
def test_reho_spheres_computation_comparison() -> None:
    """Test ReHoSpheres fit-transform implementation comparison.."""
    with SPMAuditoryTestingDatagrabber() as dg:
        # Use first subject
        subject_data = dg["sub001"]
        # Load image to memory
        fmri_img = nimg.load_img(subject_data["BOLD"]["path"])

        # Initialize marker with use_afni=False
        reho_spheres_marker_python = ReHoSpheres(
            coords=COORDINATES, radius=10.0, use_afni=False
        )
        # Fit transform marker on data
        reho_spheres_output_python = reho_spheres_marker_python.fit_transform(
            {"BOLD": {"path": "/tmp", "data": fmri_img, "meta": {}}}
        )
        # Get BOLD output
        reho_spheres_output_bold_python = reho_spheres_output_python["BOLD"]

        # Initialize marker with use_afni=True
        reho_spheres_marker_afni = ReHoSpheres(
            coords=COORDINATES, radius=10.0, use_afni=True
        )
        # Fit transform marker on data
        reho_spheres_output_afni = reho_spheres_marker_afni.fit_transform(
            {"BOLD": {"path": "/tmp", "data": fmri_img, "meta": {}}}
        )
        # Get BOLD output
        reho_spheres_output_bold_afni = reho_spheres_output_afni["BOLD"]

        # Check for Pearson correlation coefficient
        r, _ = pearsonr(
            reho_spheres_output_bold_python["data"].flatten(),
            reho_spheres_output_bold_afni["data"].flatten(),
        )
        assert r >= 0.8  # 0.8 is a loose threshold


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
        meta = {
            "element": {"subject": "sub001"}
        }  # only requires element key for storing
        # Fit transform marker on data with storage
        reho_spheres_marker.fit_transform(
            input={"BOLD": {"path": "/tmp", "data": fmri_img, "meta": meta}},
            storage=reho_spheres_storage,
        )
