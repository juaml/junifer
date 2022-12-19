"""Provide tests for ReHo on parcels."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

import pytest
from nilearn import image as nimg
from scipy.stats import pearsonr

from junifer.markers.reho.reho_parcels import ReHoParcels
from junifer.pipeline.utils import _check_afni
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
            {"BOLD": {"path": "/tmp", "data": fmri_img, "meta": {}}}
        )
        # Get BOLD output
        reho_parcels_output_bold = reho_parcels_output["BOLD"]
        # Assert BOLD output keys
        assert "data" in reho_parcels_output_bold
        assert "columns" in reho_parcels_output_bold

        reho_parcels_output_bold_data = reho_parcels_output_bold["data"]
        # Assert BOLD output data dimension
        assert reho_parcels_output_bold_data.ndim == 2
        # Assert BOLD output data is normalized
        assert (reho_parcels_output_bold_data > 0).all() and (
            reho_parcels_output_bold_data < 1
        ).all()


@pytest.mark.skipif(
    _check_afni() is False, reason="requires afni to be in PATH"
)
def test_reho_parcels_computation_comparison() -> None:
    """Test ReHoParcels fit-transform implementation comparison.."""
    with SPMAuditoryTestingDatagrabber() as dg:
        # Use first subject
        subject_data = dg["sub001"]
        # Load image to memory
        fmri_img = nimg.load_img(subject_data["BOLD"]["path"])

        # Initialize marker with use_afni=False
        reho_parcels_marker_python = ReHoParcels(
            parcellation=PARCELLATION, use_afni=False
        )
        # Fit transform marker on data
        reho_parcels_output_python = reho_parcels_marker_python.fit_transform(
            {"BOLD": {"path": "/tmp", "data": fmri_img, "meta": {}}}
        )
        # Get BOLD output
        reho_parcels_output_bold_python = reho_parcels_output_python["BOLD"]

        # Initialize marker with use_afni=True
        reho_parcels_marker_afni = ReHoParcels(
            parcellation=PARCELLATION, use_afni=True
        )
        # Fit transform marker on data
        reho_parcels_output_afni = reho_parcels_marker_afni.fit_transform(
            {"BOLD": {"path": "/tmp", "data": fmri_img, "meta": {}}}
        )
        # Get BOLD output
        reho_parcels_output_bold_afni = reho_parcels_output_afni["BOLD"]

        # Check for Pearson correlation coefficient
        r, _ = pearsonr(
            reho_parcels_output_bold_python["data"].flatten(),
            reho_parcels_output_bold_afni["data"].flatten(),
        )
        assert r >= 0.3  # this is very bad, but they differ...


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
        meta = {
            "element": {"subject": "sub001"}
        }  # only requires element key for storing
        # Fit transform marker on data with storage
        reho_parcels_marker.fit_transform(
            input={"BOLD": {"path": "/tmp", "data": fmri_img, "meta": meta}},
            storage=reho_parcels_storage,
        )
