"""Provide tests for DataladAOMICID1000 DataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Vera Komeyer <v.komeyer@fz-juelich.de>
#          Xuan Li <xu.li@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import List, Union

import pytest

from junifer.datagrabber.aomic.id1000 import DataladAOMICID1000


URI = "https://gin.g-node.org/juaml/datalad-example-aomic1000"


def test_DataladAOMICID1000() -> None:
    """Test DataladAOMICID1000 DataGrabber."""
    dg = DataladAOMICID1000()
    # Set URI to Gin
    dg.uri = URI

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

        # assert BOLD_mask
        assert out["BOLD_mask"]["path"].exists()

        # asserts type "T1w"
        assert "T1w" in out

        assert (
            out["T1w"]["path"].name
            == f"sub-{test_element}_space-MNI152NLin2009cAsym_"
            "desc-preproc_T1w.nii.gz"
        )

        assert out["T1w"]["path"].exists()
        assert out["T1w"]["path"].is_file()

        # asserts T1w_mask
        assert out["T1w_mask"]["path"].exists()

        # asserts type "probseg_CSF"
        assert "probseg_CSF" in out

        assert (
            out["probseg_CSF"]["path"].name
            == f"sub-{test_element}_space-MNI152NLin2009cAsym_label-"
            "CSF_probseg.nii.gz"
        )

        assert out["probseg_CSF"]["path"].exists()
        assert out["probseg_CSF"]["path"].is_file()

        # asserts type "probseg_GM"
        assert "probseg_GM" in out

        assert (
            out["probseg_GM"]["path"].name
            == f"sub-{test_element}_space-MNI152NLin2009cAsym_label-"
            "GM_probseg.nii.gz"
        )

        assert out["probseg_GM"]["path"].exists()
        assert out["probseg_GM"]["path"].is_file()

        # asserts type "probseg_WM"
        assert "probseg_WM" in out

        assert (
            out["probseg_WM"]["path"].name
            == f"sub-{test_element}_space-MNI152NLin2009cAsym_label-"
            "WM_probseg.nii.gz"
        )

        assert out["probseg_WM"]["path"].exists()
        assert out["probseg_WM"]["path"].is_file()

        # asserts type "DWI"
        assert "DWI" in out

        assert (
            out["DWI"]["path"].name
            == f"sub-{test_element}_desc-preproc_dwi.nii.gz"
        )

        assert out["DWI"]["path"].exists()
        assert out["DWI"]["path"].is_file()

        # asserts meta
        assert "meta" in out["BOLD"]
        meta = out["BOLD"]["meta"]
        assert "element" in meta
        assert "subject" in meta["element"]
        assert test_element == meta["element"]["subject"]


@pytest.mark.parametrize(
    "types",
    [
        "BOLD",
        "BOLD_confounds",
        "T1w",
        "probseg_CSF",
        "probseg_GM",
        "probseg_WM",
        "DWI",
        ["BOLD", "BOLD_confounds"],
        ["T1w", "probseg_CSF"],
        ["probseg_GM", "probseg_WM"],
        ["DWI", "BOLD"],
    ],
)
def test_DataladAOMICID1000_partial_data_access(
    types: Union[str, List[str]],
) -> None:
    """Test DataladAOMICID1000 DataGrabber partial data access.

    Parameters
    ----------
    types : str or list of str
        The parametrized types.

    """
    dg = DataladAOMICID1000(types=types)
    # Set URI to Gin
    dg.uri = URI

    with dg:
        # Get all elements
        all_elements = dg.get_elements()
        # Get test element
        test_element = all_elements[0]
        # Get test element data
        out = dg[test_element]
        # Assert data type
        if isinstance(types, list):
            for type_ in types:
                assert type_ in out
        else:
            assert types in out


def test_DataladAOMICID1000_incorrect_data_type() -> None:
    """Test DataladAOMICID1000 DataGrabber incorrect data type."""
    with pytest.raises(
        ValueError, match="`patterns` must contain all `types`"
    ):
        _ = DataladAOMICID1000(types="Scooby-Doo")
