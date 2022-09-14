"""Provide tests for aomic1000."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Vera Komeyer <v.komeyer@fz-juelich.de>
# License: AGPL

from junifer.datagrabber.aomic1000 import DataladAOMIC1000
# import pytest


def test_aomic1000_datagrabber() -> None:
    """Test datalad AOMIC1000 datagrabber."""
    with DataladAOMIC1000() as dg:
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
        # assert "task" in meta["element"]
        assert test_element == meta["element"]["subject"]
        # assert test_element[1] == meta["element"]["task"]


# # test replacements (subject, tasks)
# # task = moviewatching, none
# def test_aomic1000_errors() -> None:
#     """Test AOMIC1000 errors."""

#     # test if value errro raised with wrong task input
#     with pytest.raises(ValueError, match=r"not a valid AOMIC fMRI"):
#         DataladAOMIC1000(task="onewrong")

#     # test if value errro raised with wrong task input
#     with pytest.raises(ValueError, match=r"not a valid AOMIC fMRI"):
#         DataladAOMIC1000(task=["onewrong", "twowrong"])
