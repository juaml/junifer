"""Provide test for parcel aggregation."""

# Authors: Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Kaustubh R. Patil <k.patil@fz-juelich.de>
# License: AGPL

from nilearn import datasets, image

from junifer.markers.functional_connectivity_spheres import (
    FunctionalConnectivitySpheres,
)


def test_FunctionalConnectivitySpheres() -> None:
    """Test FunctionalConnectivitySpheres."""

    # get a dataset
    ni_data = datasets.fetch_spm_auditory(subject_id="sub001")
    fmri_img = image.concat_imgs(ni_data.func)  # type: ignore

    fc = FunctionalConnectivitySpheres(
        coords="DMNBuckner", radius=5.0, cor_method="correlation"
    )
    out = fc.compute({"data": fmri_img})

    assert "data" in out
    assert "row_names" in out
    assert "col_names" in out
    assert out["data"].shape[0] == 6
    assert out["data"].shape[1] == 6
    assert len(set(out["row_names"])) == 6
    assert len(set(out["col_names"])) == 6
