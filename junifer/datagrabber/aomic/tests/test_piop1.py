"""Provide tests for aomic piop1."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Vera Komeyer <v.komeyer@fz-juelich.de>
#          Xuan Li <xu.li@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL

import pytest

from junifer.datagrabber.aomic.piop1 import DataladAOMICPIOP1
from junifer.utils import configure_logging


def test_aomic_piop1_datagrabber() -> None:
    """Test datalad AOMICPIOP1 datagrabber."""
    configure_logging(level="DEBUG")

    uri_PIOP1 = "https://gin.g-node.org/juaml/datalad-example-aomicpiop1"
    task_params = [None, "restingstate"]

    for task_param in task_params:
        dg = DataladAOMICPIOP1(tasks=task_param)

        # change uri here to use fake data instead of real dataset
        dg.uri = uri_PIOP1

        with dg:
            all_elements = dg.get_elements()
            test_element = all_elements[0]
            sub, task = test_element

            out = dg[test_element]

            # asserts type "BOLD"
            assert "BOLD" in out

            # depending on task 'acquisition is different'
            task_acqs = {
                "anticipation": "seq",
                "emomatching": "seq",
                "faces": "mb3",
                "gstroop": "seq",
                "restingstate": "mb3",
                "workingmemory": "seq",
            }
            acq = task_acqs[task]
            new_task = f"{task}_acq-{acq}"
            assert (
                out["BOLD"]["path"].name == f"sub-{sub}_task-{new_task}_"
                "space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz"
            )

            assert out["BOLD"]["path"].exists()
            assert out["BOLD"]["path"].is_file()

            # asserts type "BOLD_confounds"
            assert "BOLD_confounds" in out

            assert (
                out["BOLD_confounds"]["path"].name
                == f"sub-{sub}_task-{new_task}_"
                "desc-confounds_regressors.tsv"
            )

            assert out["BOLD_confounds"]["path"].exists()
            assert out["BOLD_confounds"]["path"].is_file()

            # asserts type "T1w"
            assert "T1w" in out

            assert (
                out["T1w"]["path"].name
                == f"sub-{sub}_space-MNI152NLin2009cAsym_"
                "desc-preproc_T1w.nii.gz"
            )

            assert out["T1w"]["path"].exists()
            assert out["T1w"]["path"].is_file()

            # asserts type "probseg_CSF"
            assert "probseg_CSF" in out

            assert (
                out["probseg_CSF"]["path"].name
                == f"sub-{sub}_space-MNI152NLin2009cAsym_label-"
                "CSF_probseg.nii.gz"
            )

            assert out["probseg_CSF"]["path"].exists()
            assert out["probseg_CSF"]["path"].is_file()

            # asserts type "probseg_GM"
            assert "probseg_GM" in out

            assert (
                out["probseg_GM"]["path"].name
                == f"sub-{sub}_space-MNI152NLin2009cAsym_label-"
                "GM_probseg.nii.gz"
            )

            assert out["probseg_GM"]["path"].exists()
            assert out["probseg_GM"]["path"].is_file()

            # asserts type "probseg_WM"
            assert "probseg_WM" in out

            assert (
                out["probseg_WM"]["path"].name
                == f"sub-{sub}_space-MNI152NLin2009cAsym_label-"
                "WM_probseg.nii.gz"
            )

            assert out["probseg_WM"]["path"].exists()
            assert out["probseg_WM"]["path"].is_file()

            # asserts type "DWI"
            assert "DWI" in out

            assert (
                out["DWI"]["path"].name == f"sub-{sub}_desc-preproc_dwi.nii.gz"
            )

            assert out["DWI"]["path"].exists()
            assert out["DWI"]["path"].is_file()

            # asserts meta
            assert "meta" in out["BOLD"]
            meta = out["BOLD"]["meta"]
            assert "element" in meta
            assert "subject" in meta["element"]
            assert sub == meta["element"]["subject"]


def test_piop1_invalid_tasks():
    """Test whether invalid task fails."""
    with pytest.raises(
        ValueError,
        match=(
            "thisisnotarealtask is not a valid task in "
            "the AOMIC PIOP1 dataset!"
        ),
    ):

        DataladAOMICPIOP1(tasks="thisisnotarealtask")
