"""Provide tests for temporal signal-to-noise ratio using parcellation."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL

from pathlib import Path

from nilearn import datasets, image

from junifer.markers.temporal_snr import TemporalSNRParcels
from junifer.storage import SQLiteFeatureStorage


def test_TemporalSNRParcels(tmp_path: Path) -> None:
    """Test TemporalSNRParcels.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    # get a dataset
    ni_data = datasets.fetch_spm_auditory(subject_id="sub001")
    fmri_img = image.concat_imgs(ni_data.func)  # type: ignore

    tsnr_parcels = TemporalSNRParcels(parcellation="Schaefer100x7")
    all_out = tsnr_parcels.fit_transform(
        {"BOLD": {"data": fmri_img, "meta": {}, "space": "MNI"}}
    )

    out = all_out["BOLD"]

    assert "data" in out
    assert "col_names" in out

    assert out["data"].shape[0] == 1
    assert out["data"].shape[1] == 100
    assert len(set(out["col_names"])) == 100

    # check correct output
    assert tsnr_parcels.get_output_type("BOLD") == "vector"

    uri = tmp_path / "test_tsnr_parcellation.sqlite"
    # Single storage, must be the uri
    storage = SQLiteFeatureStorage(uri=uri, upsert="ignore")
    meta = {"element": {"subject": "test"}, "dependencies": {"numpy"}}
    input = {"BOLD": {"data": fmri_img, "meta": meta, "space": "MNI"}}
    all_out = tsnr_parcels.fit_transform(input, storage=storage)

    features = storage.list_features()
    assert any(
        x["name"] == "BOLD_TemporalSNRParcels" for x in features.values()
    )
