"""Provide tests for temporal signal-to-noise spheres."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL

from pathlib import Path

import pytest
from nilearn import datasets, image

from junifer.markers.temporal_snr import TemporalSNRSpheres
from junifer.storage import SQLiteFeatureStorage


def test_TemporalSNRSpheres(tmp_path: Path) -> None:
    """Test TemporalSNRSpheres.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    # get a dataset
    ni_data = datasets.fetch_spm_auditory(subject_id="sub001")
    fmri_img = image.concat_imgs(ni_data.func)  # type: ignore

    tsnr_spheres = TemporalSNRSpheres(coords="DMNBuckner", radius=5.0)
    all_out = tsnr_spheres.fit_transform(
        {"BOLD": {"data": fmri_img, "meta": {}, "space": "MNI"}}
    )

    out = all_out["BOLD"]

    assert "data" in out
    assert "col_names" in out
    assert out["data"].shape[0] == 1
    assert out["data"].shape[1] == 6
    assert len(set(out["col_names"])) == 6

    # check correct output
    assert tsnr_spheres.get_output_type("BOLD") == "vector"

    uri = tmp_path / "test_tsnr_coords.sqlite"
    # Single storage, must be the uri
    storage = SQLiteFeatureStorage(uri=uri, upsert="ignore")
    meta = {
        "element": {"subject": "test"},
        "dependencies": {"numpy", "nilearn"},
    }
    input = {"BOLD": {"data": fmri_img, "meta": meta, "space": "MNI"}}
    all_out = tsnr_spheres.fit_transform(input, storage=storage)

    features = storage.list_features()
    assert any(
        x["name"] == "BOLD_TemporalSNRSpheres" for x in features.values()
    )


def test_TemporalSNRSpheres_error() -> None:
    """Test TemporalSNRSpheres errors."""
    with pytest.raises(ValueError, match="radius should be > 0"):
        TemporalSNRSpheres(coords="DMNBuckner", radius=-0.1)
