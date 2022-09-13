"""Provide test for root sum of squares of edgewise timeseries."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
#          Nicolás Nieto <n.nieto@fz-juelich.de>
#          Sami Hamdan <s.hamdan@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL
from nilearn import image
from nilearn.maskers import NiftiLabelsMasker
from junifer.testing.datagrabbers import SPMAuditoryTestingDatagrabber
from junifer.markers.etsrss import RSSETSMarker
from junifer.data import load_atlas
import pytest


def test_RSSETS() -> None:
    """Test RSS ETS."""
    atlas = "Schaefer100x17"
    test_atlas, _, _ = load_atlas(atlas)

    with SPMAuditoryTestingDatagrabber() as dg:
        out = dg['sub001']
        niimg = image.load_img(out["BOLD"]["path"])
        input_dict = {
            "BOLD": niimg,
            "path": out["BOLD"]["path"]
        }

        ets_rss = RSSETSMarker(atlas=atlas)
        new_out = ets_rss.compute(input_dict)

        test_masker = NiftiLabelsMasker(test_atlas)
        test_ts = test_masker.fit_transform(niimg)

        n_time, _ = test_ts.shape
        assert n_time == len(new_out["RSS"])


def test_get_output_kind():
    with pytest.raises(ValueError, match="Unknown input kind for"):
        atlas = "Schaefer100x17"
        input_dict = {"THIS_IS_NOT_BOLD": "THIS_IS_NOT_A_NIFTI_FILE"}
        ets_rss = RSSETSMarker(atlas=atlas)
        ets_rss.get_output_kind(input_dict)
