"""Provide tests for confound removal."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import random
import string
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
from nibabel import Nifti1Image
from nilearn._utils.niimg_conversions import check_niimg_4d

from junifer.preprocess.confounds import BaseConfoundRemover


# Set RNG seed for reproducibility
np.random.seed(1234567)


def generate_conf_name(
    size: int = 6, chars: str = string.ascii_uppercase + string.digits
) -> str:
    """Generate configuration name."""
    return "".join(random.choice(chars) for _ in range(size))


def _simu_img() -> Tuple[Nifti1Image, Nifti1Image]:
    # Random 4D volume with 100 time points
    vol = 100 + 10 * np.random.randn(5, 5, 2, 100)
    img = Nifti1Image(vol, np.eye(4))
    # Create an nifti image with the data, and corresponding mask
    mask = Nifti1Image(np.ones([5, 5, 2]), np.eye(4))
    return img, mask


# TODO: split the tests
def test_baseconfoundremover() -> None:
    """Test BaseConfoundRemover."""
    # Generate a simulated BOLD img
    siimg, simsk = _simu_img()

    # generate random confound dataframe with Felix's column naming

    motion_basic = [f"RP.{i}" for i in range(1, 7)]
    motion_power2 = [f"RP^2.{i}" for i in range(1, 7)]
    motion_derivatives = [f"DRP.{i}" for i in range(1, 7)]
    motion_full = [f"DRP^2.{i}" for i in range(1, 7)]

    wm_csf_basic = ["WM", "CSF"]
    wm_csf_power2 = ["WM^2", "CSF^2"]
    wm_csf_derivatives = ["DWM", "DCSF"]
    wm_csf_full = ["DWM^2", "DCSF^2"]

    gs_basic = ["GS"]
    gs_power2 = ["GS^2"]
    gs_derivatives = ["DGS"]
    gs_full = ["DGS^2"]

    confound_column_names = []

    confound_column_names.append("FD")  # spike

    confound_column_names.extend(motion_basic)
    confound_column_names.extend(motion_power2)
    confound_column_names.extend(motion_derivatives)
    confound_column_names.extend(motion_full)

    confound_column_names.extend(wm_csf_basic)
    confound_column_names.extend(wm_csf_power2)
    confound_column_names.extend(wm_csf_derivatives)
    confound_column_names.extend(wm_csf_full)

    confound_column_names.extend(gs_basic)
    confound_column_names.extend(gs_power2)
    confound_column_names.extend(gs_derivatives)
    confound_column_names.extend(gs_full)

    # add some random irrelevant confounds
    for _ in range(10):
        confound_column_names.append(generate_conf_name())

    np.random.shuffle(confound_column_names)
    n_cols = len(confound_column_names)
    confounds_df = pd.DataFrame(
        np.random.randint(0, 100, size=(100, n_cols)),
        columns=confound_column_names,
    )

    # Generate spec from Felix's column naming
    spec = {
        "motion": {
            "basic": motion_basic,
            "power2": motion_basic + motion_power2,
            "derivatives": motion_basic + motion_derivatives,
            "full": motion_basic
            + motion_derivatives
            + motion_power2
            + motion_full,
        },
        "wm_csf": {
            "basic": wm_csf_basic,
            "power2": wm_csf_basic + wm_csf_power2,
            "derivatives": wm_csf_basic + wm_csf_derivatives,
            "full": wm_csf_basic
            + wm_csf_derivatives
            + wm_csf_power2
            + wm_csf_full,
        },
        "global_signal": {
            "basic": gs_basic,
            "power2": gs_basic + gs_power2,
            "derivatives": gs_basic + gs_derivatives,
            "full": gs_basic + gs_derivatives + gs_power2 + gs_full,
        },
    }

    # generate a junifer pipeline data object dictionary
    input_data_obj = {}
    input_data_obj["meta"] = {}
    input_data_obj["BOLD"] = {}
    input_data_obj["BOLD"]["data"] = siimg
    input_data_obj["confounds"] = {}
    input_data_obj["confounds"]["path"] = Path("/test.df")
    input_data_obj["confounds"]["data"] = confounds_df
    input_data_obj["confounds"]["names"] = {}
    input_data_obj["confounds"]["names"]["spec"] = spec
    input_data_obj["confounds"]["names"]["spike"] = "FD"

    # generate confound removal strategies with varying numbers of parameters

    # Test #1: 36 params, no derivatives to compute, no spike
    # 36 params
    strat1 = {"motion": "full", "wm_csf": "full", "global_signal": "full"}

    cr = BaseConfoundRemover(
        strategy=strat1, spike=None, mask_img=simsk, t_r=0.75
    )
    cr.validate_input(input_data_obj.keys())
    out_type = cr.get_output_kind(input_data_obj.keys())

    assert "BOLD" in out_type

    # Check if the input data is valid
    cr._validate_data(input_data_obj)

    # Check that the confounds are picked correctly:
    t_df = cr._pick_confounds(input_data_obj["confounds"])
    assert len(t_df.columns) == 36
    assert all(x in t_df.columns for x in motion_basic)
    assert all(x in t_df.columns for x in motion_power2)
    assert all(x in t_df.columns for x in motion_derivatives)
    assert all(x in t_df.columns for x in motion_full)
    assert all(x in t_df.columns for x in wm_csf_basic)
    assert all(x in t_df.columns for x in wm_csf_power2)
    assert all(x in t_df.columns for x in wm_csf_derivatives)
    assert all(x in t_df.columns for x in wm_csf_full)
    assert all(x in t_df.columns for x in gs_basic)
    assert all(x in t_df.columns for x in gs_power2)
    assert all(x in t_df.columns for x in gs_derivatives)
    assert all(x in t_df.columns for x in gs_full)
    assert "FD" not in t_df.columns
    assert "spike" not in t_df.columns

    # Test #2: 24 params, no derivatives to compute, no spike
    # 24 params
    strat2 = {
        "motion": "full",
    }

    cr = BaseConfoundRemover(
        strategy=strat2, spike=None, mask_img=simsk, t_r=0.75
    )
    cr.validate_input(input_data_obj.keys())
    out_type = cr.get_output_kind(input_data_obj.keys())

    assert "BOLD" in out_type

    # Check if the input data is valid
    cr._validate_data(input_data_obj)

    # Check that the confounds are picked correctly:
    t_df = cr._pick_confounds(input_data_obj["confounds"])
    assert len(t_df.columns) == 24
    assert all(x in t_df.columns for x in motion_basic)
    assert all(x in t_df.columns for x in motion_power2)
    assert all(x in t_df.columns for x in motion_derivatives)
    assert all(x in t_df.columns for x in motion_full)
    assert all(x not in t_df.columns for x in wm_csf_basic)
    assert all(x not in t_df.columns for x in wm_csf_power2)
    assert all(x not in t_df.columns for x in wm_csf_derivatives)
    assert all(x not in t_df.columns for x in wm_csf_full)
    assert all(x not in t_df.columns for x in gs_basic)
    assert all(x not in t_df.columns for x in gs_power2)
    assert all(x not in t_df.columns for x in gs_derivatives)
    assert all(x not in t_df.columns for x in gs_full)
    assert "FD" not in t_df.columns
    assert "spike" not in t_df.columns

    # Test #3: 9 params, no derivatives to compute, no spike
    strat3 = {"motion": "basic", "wm_csf": "basic", "global_signal": "basic"}

    cr = BaseConfoundRemover(
        strategy=strat3, spike=None, mask_img=simsk, t_r=0.75
    )
    cr.validate_input(input_data_obj.keys())
    out_type = cr.get_output_kind(input_data_obj.keys())

    assert "BOLD" in out_type

    # Check if the input data is valid
    cr._validate_data(input_data_obj)

    # Check that the confounds are picked correctly:
    t_df = cr._pick_confounds(input_data_obj["confounds"])
    assert len(t_df.columns) == 9
    assert all(x in t_df.columns for x in motion_basic)
    assert all(x not in t_df.columns for x in motion_power2)
    assert all(x not in t_df.columns for x in motion_derivatives)
    assert all(x not in t_df.columns for x in motion_full)
    assert all(x in t_df.columns for x in wm_csf_basic)
    assert all(x not in t_df.columns for x in wm_csf_power2)
    assert all(x not in t_df.columns for x in wm_csf_derivatives)
    assert all(x not in t_df.columns for x in wm_csf_full)
    assert all(x in t_df.columns for x in gs_basic)
    assert all(x not in t_df.columns for x in gs_power2)
    assert all(x not in t_df.columns for x in gs_derivatives)
    assert all(x not in t_df.columns for x in gs_full)
    assert "FD" not in t_df.columns
    assert "spike" not in t_df.columns

    # Test #4: 6 params, no derivatives to compute, no spike
    strat4 = {
        "motion": "basic",
    }
    cr = BaseConfoundRemover(
        strategy=strat4, spike=None, mask_img=simsk, t_r=0.75
    )
    cr.validate_input(input_data_obj.keys())
    out_type = cr.get_output_kind(input_data_obj.keys())

    assert "BOLD" in out_type

    # Check if the input data is valid
    cr._validate_data(input_data_obj)

    # Check that the confounds are picked correctly:
    t_df = cr._pick_confounds(input_data_obj["confounds"])
    assert len(t_df.columns) == 6
    assert all(x in t_df.columns for x in motion_basic)
    assert all(x not in t_df.columns for x in motion_power2)
    assert all(x not in t_df.columns for x in motion_derivatives)
    assert all(x not in t_df.columns for x in motion_full)
    assert all(x not in t_df.columns for x in wm_csf_basic)
    assert all(x not in t_df.columns for x in wm_csf_power2)
    assert all(x not in t_df.columns for x in wm_csf_derivatives)
    assert all(x not in t_df.columns for x in wm_csf_full)
    assert all(x not in t_df.columns for x in gs_basic)
    assert all(x not in t_df.columns for x in gs_power2)
    assert all(x not in t_df.columns for x in gs_derivatives)
    assert all(x not in t_df.columns for x in gs_full)
    assert "FD" not in t_df.columns
    assert "spike" not in t_df.columns

    # Test #5: 2 params, no derivatives to compute, no spike
    strat5 = {
        "wm_csf": "basic",
    }
    cr = BaseConfoundRemover(
        strategy=strat5, spike=None, mask_img=simsk, t_r=0.75
    )
    cr.validate_input(input_data_obj.keys())
    out_type = cr.get_output_kind(input_data_obj.keys())

    assert "BOLD" in out_type

    # Check if the input data is valid
    cr._validate_data(input_data_obj)

    # Check that the confounds are picked correctly:
    t_df = cr._pick_confounds(input_data_obj["confounds"])
    assert len(t_df.columns) == 2
    assert all(x not in t_df.columns for x in motion_basic)
    assert all(x not in t_df.columns for x in motion_power2)
    assert all(x not in t_df.columns for x in motion_derivatives)
    assert all(x not in t_df.columns for x in motion_full)
    assert all(x in t_df.columns for x in wm_csf_basic)
    assert all(x not in t_df.columns for x in wm_csf_power2)
    assert all(x not in t_df.columns for x in wm_csf_derivatives)
    assert all(x not in t_df.columns for x in wm_csf_full)
    assert all(x not in t_df.columns for x in gs_basic)
    assert all(x not in t_df.columns for x in gs_power2)
    assert all(x not in t_df.columns for x in gs_derivatives)
    assert all(x not in t_df.columns for x in gs_full)
    assert "FD" not in t_df.columns
    assert "spike" not in t_df.columns

    out = cr.fit_transform(input_data_obj)
    check_niimg_4d(out["BOLD"]["data"])
    # TODO: check meta

    # Test #6: 12 params, derivatives to compute, spike
    to_select = [
        x for x in confounds_df.columns if x not in motion_derivatives
    ]
    no_d_df = confounds_df[to_select]
    input_data_obj["confounds"]["data"] = no_d_df

    derivatives = {f"D{x}": x for x in motion_basic}

    input_data_obj["confounds"]["names"]["derivatives"] = derivatives

    strat6 = {
        "motion": "derivatives",
    }
    cr = BaseConfoundRemover(
        strategy=strat6, spike=0.75, mask_img=simsk, t_r=0.75
    )
    cr.validate_input(input_data_obj.keys())
    out_type = cr.get_output_kind(input_data_obj.keys())

    assert "BOLD" in out_type

    # Check if the input data is valid
    cr._validate_data(input_data_obj)

    # Check that the confounds are picked correctly:
    t_df = cr._pick_confounds(input_data_obj["confounds"])
    assert len(t_df.columns) == 13
    assert all(x in t_df.columns for x in motion_basic)
    assert all(x not in t_df.columns for x in motion_power2)
    assert all(x in t_df.columns for x in motion_derivatives)
    assert all(x not in t_df.columns for x in motion_full)
    assert all(x not in t_df.columns for x in wm_csf_basic)
    assert all(x not in t_df.columns for x in wm_csf_power2)
    assert all(x not in t_df.columns for x in wm_csf_derivatives)
    assert all(x not in t_df.columns for x in wm_csf_full)
    assert all(x not in t_df.columns for x in gs_basic)
    assert all(x not in t_df.columns for x in gs_power2)
    assert all(x not in t_df.columns for x in gs_derivatives)
    assert all(x not in t_df.columns for x in gs_full)
    assert "FD" not in t_df.columns
    assert "spike" in t_df.columns
