"""Provide tests for aomic1000."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Vera Komeyer <v.komeyer@fz-juelich.de>
#          Xuan Li <xu.li@fz-juelich.de>
# License: AGPL

from junifer.datagrabber.aomic1000 import DataladAOMIC1000
from junifer.utils import configure_logging


uri = "git@gin.g-node.org:/juaml/datalad-example-aomic1000.git"


def test_aomic1000_datagrabber() -> None:
    """Test datalad AOMIC1000 datagrabber."""
    configure_logging(level="DEBUG")
    dg = DataladAOMIC1000()
    dg.uri = uri  # change uri here to use fake data instead of real dataset
    with dg:
        all_elements = dg.get_elements()
        test_element = all_elements[0]

        out = dg[test_element]

        # asserts type "BOLD"
        assert "BOLD" in out

        assert (
            out["BOLD"]["path"].name
            == f"sub-{test_element}_task-moviewatching_"
            "space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz"
        )

        assert out["BOLD"]["path"].exists()
        assert out["BOLD"]["path"].is_file()

        # asserts type "BOLD_confounds"
        assert "BOLD_confounds" in out

        assert (
            out["BOLD_confounds"]["path"].name
            == f"sub-{test_element}_task-moviewatching_"
            "desc-confounds_regressors.tsv"
        )

        assert out["BOLD_confounds"]["path"].exists()
        assert out["BOLD_confounds"]["path"].is_file()

        # asserts type "ANAT"
        assert "ANAT" in out

        assert (
            out["ANAT"]["path"].name
            == f"sub-{test_element}_space-MNI152NLin2009cAsym_"
            "desc-preproc_T1w.nii.gz"
        )

        assert out["ANAT"]["path"].exists()
        assert out["ANAT"]["path"].is_file()

        # asserts type "ANAT_probseg_CSF"
        assert "ANAT_probseg_CSF" in out

        assert (
            out["ANAT_probseg_CSF"]["path"].name
            == f"sub-{test_element}_space-MNI152NLin2009cAsym_label-"
            "CSF_probseg.nii.gz"
        )

        assert out["ANAT_probseg_CSF"]["path"].exists()
        assert out["ANAT_probseg_CSF"]["path"].is_file()

        # asserts type "ANAT_probseg_GM"
        assert "ANAT_probseg_GM" in out

        assert (
            out["ANAT_probseg_GM"]["path"].name
            == f"sub-{test_element}_space-MNI152NLin2009cAsym_label-"
            "GM_probseg.nii.gz"
        )

        assert out["ANAT_probseg_GM"]["path"].exists()
        assert out["ANAT_probseg_GM"]["path"].is_file()

        # asserts type "ANAT_probseg_WM"
        assert "ANAT_probseg_WM" in out

        assert (
            out["ANAT_probseg_WM"]["path"].name
            == f"sub-{test_element}_space-MNI152NLin2009cAsym_label-"
            "WM_probseg.nii.gz"
        )

        assert out["ANAT_probseg_WM"]["path"].exists()
        assert out["ANAT_probseg_WM"]["path"].is_file()

        # asserts type "DWI"
        assert "DWI" in out

        assert (
            out["DWI"]["path"].name
            == f"sub-{test_element}_desc-preproc_dwi.nii.gz"
        )

        assert out["DWI"]["path"].exists()
        assert out["DWI"]["path"].is_file()

        # asserts meta
        assert "meta" in out
        meta = out["meta"]
        assert "element" in meta
        assert "subject" in meta["element"]
        assert test_element == meta["element"]["subject"]
