"""Provide tests for fMRIPrepConfoundRemover."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import typing

import nibabel as nib
import numpy as np
import pandas as pd
import pytest
from nilearn._utils.exceptions import DimensionError
from numpy.testing import assert_array_equal, assert_raises
from pandas.testing import assert_frame_equal

from junifer.datareader import DefaultDataReader
from junifer.preprocess.confounds import fMRIPrepConfoundRemover
from junifer.testing import get_testing_data
from junifer.testing.datagrabbers import (
    OasisVBMTestingDatagrabber,
    PartlyCloudyTestingDataGrabber,
)


def test_fMRIPrepConfoundRemover_init() -> None:
    """Test fMRIPrepConfoundRemover init."""

    with pytest.raises(ValueError, match="keys must be strings"):
        fMRIPrepConfoundRemover(strategy={1: "full"})  # type: ignore

    with pytest.raises(ValueError, match="values must be strings"):
        fMRIPrepConfoundRemover(strategy={"motion": 1})  # type: ignore

    with pytest.raises(ValueError, match="component names"):
        fMRIPrepConfoundRemover(strategy={"wrong": "full"})

    with pytest.raises(ValueError, match="confound types"):
        fMRIPrepConfoundRemover(strategy={"motion": "wrong"})


def test_fMRIPrepConfoundRemover_validate_input() -> None:
    """Test fMRIPrepConfoundRemover validate_input."""
    confound_remover = fMRIPrepConfoundRemover()

    # Input is valid when both BOLD and BOLD_confounds are present

    input = ["T1w"]
    with pytest.raises(ValueError, match="not have the required data"):
        confound_remover.validate_input(input)

    input = ["BOLD"]
    with pytest.raises(ValueError, match="not have the required data"):
        confound_remover.validate_input(input)

    input = ["BOLD", "T1w"]
    with pytest.raises(ValueError, match="not have the required data"):
        confound_remover.validate_input(input)

    input = ["BOLD", "T1w", "BOLD_confounds"]
    confound_remover.validate_input(input)


def test_fMRIPrepConfoundRemover_get_output_type() -> None:
    """Test fMRIPrepConfoundRemover validate_input."""
    confound_remover = fMRIPrepConfoundRemover()
    inputs = [
        ["BOLD", "T1w", "BOLD_confounds"],
        ["BOLD", "VBM_GM", "BOLD_confounds"],
        ["BOLD", "BOLD_confounds"],
    ]
    # Confound remover works in place
    for input in inputs:
        assert confound_remover.get_output_type(input) == input


def test_fMRIPrepConfoundRemover__map_adhoc_to_fmriprep() -> None:
    """Test fMRIPrepConfoundRemover adhoc to fmriprep spec mapping."""
    confound_remover = fMRIPrepConfoundRemover()
    # Use non fmriprep variable names
    adhoc_names = [f"var{i}" for i in range(6)]
    adhoc_df = pd.DataFrame(np.random.randn(10, 6), columns=adhoc_names)

    # map them to valid variable names
    fmriprep_names = [
        "trans_x",
        "trans_y",
        "trans_z",
        "rot_x",
        "rot_y",
        "rot_z",
    ]

    # Build mappings dictionary
    mappings = {x: y for x, y in zip(adhoc_names, fmriprep_names)}
    input = {
        "mappings": {"fmriprep": mappings},
        "data": adhoc_df,
    }

    confound_remover._map_adhoc_to_fmriprep(input)
    # This should work in-place
    assert adhoc_df.columns.tolist() == fmriprep_names


def test_fMRIPrepConfoundRemover__process_fmriprep_spec() -> None:
    """Test fMRIPrepConfoundRemover fmriprep spec processing."""

    # Test one strategy, full, no spike
    confound_remover = fMRIPrepConfoundRemover(strategy={"wm_csf": "full"})

    var_names = [
        "csf",
        "white_matter",
        "csf_power2",
        "white_matter_power2",
        "csf_derivative1",
        "white_matter_derivative1",
        "csf_derivative1_power2",
        "white_matter_derivative1_power2",
    ]

    confounds_df = pd.DataFrame(
        np.random.randn(7, len(var_names)), columns=var_names
    )

    out = confound_remover._process_fmriprep_spec({"data": confounds_df})
    to_select, sq_to_compute, der_to_compute, spike_name = out
    assert set(to_select) == set(var_names)
    assert len(sq_to_compute) == 0
    assert len(der_to_compute) == 0
    assert spike_name == "framewise_displacement"

    # Same strategy, but derivatives are not present
    var_names = ["csf", "white_matter", "csf_power2", "white_matter_power2"]
    missing_der_names = ["csf_derivative1", "white_matter_derivative1"]
    missing_sq_names = [
        "csf_derivative1_power2",
        "white_matter_derivative1_power2",
    ]

    all_names = var_names + missing_der_names + missing_sq_names

    confounds_df = pd.DataFrame(
        np.random.randn(7, len(var_names)), columns=var_names
    )
    out = confound_remover._process_fmriprep_spec({"data": confounds_df})
    to_select, sq_to_compute, der_to_compute, spike_name = out
    assert set(to_select) == set(all_names)
    assert set(sq_to_compute) == set(missing_sq_names)
    assert set(der_to_compute) == set(missing_der_names)
    assert spike_name == "framewise_displacement"

    # Same strategy, with spike, only basics are present
    confound_remover = fMRIPrepConfoundRemover(
        strategy={"wm_csf": "full"}, spike=0.2
    )

    var_names = ["csf", "white_matter"]
    missing_der_names = ["csf_derivative1", "white_matter_derivative1"]
    missing_sq_names = [
        "csf_power2",
        "white_matter_power2",
        "csf_derivative1_power2",
        "white_matter_derivative1_power2",
    ]

    all_names = var_names + missing_der_names + missing_sq_names

    confounds_df = pd.DataFrame(
        np.random.randn(7, len(var_names) + 1),
        columns=var_names + ["framewise_displacement"],
    )
    out = confound_remover._process_fmriprep_spec({"data": confounds_df})
    to_select, sq_to_compute, der_to_compute, spike_name = out
    assert set(to_select) == set(all_names)
    assert set(sq_to_compute) == set(missing_sq_names)
    assert set(der_to_compute) == set(missing_der_names)
    assert spike_name == "framewise_displacement"

    # Two component strategy, mixed confounds, no spike
    confound_remover = fMRIPrepConfoundRemover(
        strategy={"wm_csf": "power2", "global_signal": "derivatives"}
    )

    var_names = ["csf", "white_matter", "global_signal"]
    missing_der_names = ["global_signal_derivative1"]
    missing_sq_names = [
        "csf_power2",
        "white_matter_power2",
    ]

    all_names = var_names + missing_der_names + missing_sq_names

    confounds_df = pd.DataFrame(
        np.random.randn(7, len(var_names)), columns=var_names
    )
    out = confound_remover._process_fmriprep_spec({"data": confounds_df})
    to_select, sq_to_compute, der_to_compute, spike_name = out
    assert set(to_select) == set(all_names)
    assert set(sq_to_compute) == set(missing_sq_names)
    assert set(der_to_compute) == set(missing_der_names)
    assert spike_name == "framewise_displacement"

    # Test for wrong columns/strategy pairs

    confound_remover = fMRIPrepConfoundRemover(
        strategy={"wm_csf": "full"}, spike=0.2
    )
    var_names = ["csf"]
    confounds_df = pd.DataFrame(
        np.random.randn(7, len(var_names)), columns=var_names
    )

    msg = r"Missing basic confounds: \['white_matter'\]"
    with pytest.raises(ValueError, match=msg):
        confound_remover._process_fmriprep_spec({"data": confounds_df})

    var_names = ["csf", "white_matter"]
    confounds_df = pd.DataFrame(
        np.random.randn(7, len(var_names)), columns=var_names
    )

    msg = r"Missing framewise_displacement"
    with pytest.raises(ValueError, match=msg):
        confound_remover._process_fmriprep_spec({"data": confounds_df})


def test_fMRIPrepConfoundRemover__pick_confounds_adhoc() -> None:
    """Test fMRIPrepConfoundRemover pick confounds on adhoc confounds."""
    confound_remover = fMRIPrepConfoundRemover(strategy={"wm_csf": "full"})
    # Use non fmriprep variable names
    adhoc_names = [f"var{i}" for i in range(2)]
    adhoc_df = pd.DataFrame(np.random.randn(10, 2), columns=adhoc_names)

    # map them to valid variable names
    fmriprep_names = ["csf", "white_matter"]
    fmriprep_all_vars = [
        "csf",
        "white_matter",
        "csf_power2",
        "white_matter_power2",
        "csf_derivative1",
        "white_matter_derivative1",
        "csf_derivative1_power2",
        "white_matter_derivative1_power2",
    ]

    # Build mappings dictionary
    mappings = {x: y for x, y in zip(adhoc_names, fmriprep_names)}
    input = {
        "mappings": {"fmriprep": mappings},
        "data": adhoc_df,
        "format": "adhoc",
    }

    out = confound_remover._pick_confounds(input)
    assert set(out.columns) == set(fmriprep_all_vars)


def test_FMRIPRepConfoundRemover__pick_confounds_fmriprep() -> None:
    """Test fMRIPrepConfoundRemover pick confounds on fmriprep confounds."""
    confound_remover = fMRIPrepConfoundRemover(
        strategy={"wm_csf": "full"}, spike=0.2
    )
    fmriprep_all_vars = [
        "csf",
        "white_matter",
        "csf_power2",
        "white_matter_power2",
        "csf_derivative1",
        "white_matter_derivative1",
        "csf_derivative1_power2",
        "white_matter_derivative1_power2",
    ]

    reader = DefaultDataReader()
    out1, out2 = None, None
    with PartlyCloudyTestingDataGrabber() as dg:
        input = dg["sub-01"]
        input = reader.fit_transform(input)
        out1 = confound_remover._pick_confounds(input["BOLD_confounds"])
        assert set(out1.columns) == set(fmriprep_all_vars + ["spike"])

    with PartlyCloudyTestingDataGrabber(reduce_confounds=False) as dg:
        input = dg["sub-01"]
        input = reader.fit_transform(input)
        out2 = confound_remover._pick_confounds(input["BOLD_confounds"])
        assert set(out2.columns) == set(fmriprep_all_vars + ["spike"])

    assert_frame_equal(out1, out2)


def test_FMRIPRepConfoundRemover__pick_confounds_fmriprep_compute() -> None:
    """Test if fmriprep returns the same derivatives/power2 as we compute."""

    confound_remover = fMRIPrepConfoundRemover(strategy={"wm_csf": "full"})
    fmriprep_all_vars = [
        "csf",
        "white_matter",
        "csf_power2",
        "white_matter_power2",
        "csf_derivative1",
        "white_matter_derivative1",
        "csf_derivative1_power2",
        "white_matter_derivative1_power2",
    ]

    t_fname = get_testing_data(
        "sub-0001_task-anticipation_acq-seq_desc-confounds_regressors.tsv"
    )
    t_full_confounds = pd.read_csv(t_fname, sep="\t")[fmriprep_all_vars]
    t_basic_confounds = t_full_confounds[["csf", "white_matter"]]

    input_basic = {"data": t_basic_confounds, "format": "fmriprep"}
    out_junifer = confound_remover._pick_confounds(input_basic)

    input_full = {"data": t_full_confounds, "format": "fmriprep"}
    out_fmriprep = confound_remover._pick_confounds(input_full)

    assert np.all(out_fmriprep.values != np.nan)
    assert_frame_equal(out_junifer, out_fmriprep)


def test_fMRIPrepConfoundRemover__validate_data() -> None:
    """Test fMRIPrepConfoundRemover validate data."""
    confound_remover = fMRIPrepConfoundRemover(strategy={"wm_csf": "full"})
    reader = DefaultDataReader()
    with OasisVBMTestingDatagrabber() as dg:
        input = dg["sub-01"]
        input = reader.fit_transform(input)
        new_input = input["VBM_GM"]
        with pytest.raises(
            DimensionError, match="incompatible dimensionality"
        ):
            confound_remover._validate_data(new_input, None)

    with PartlyCloudyTestingDataGrabber(reduce_confounds=False) as dg:
        input = dg["sub-01"]
        input = reader.fit_transform(input)
        new_input = input["BOLD"]

        with pytest.raises(ValueError, match="No extra input"):
            confound_remover._validate_data(new_input, None)
        with pytest.raises(ValueError, match="No BOLD_confounds provided"):
            confound_remover._validate_data(new_input, {})
        with pytest.raises(
            ValueError, match="No BOLD_confounds data provided"
        ):
            confound_remover._validate_data(new_input, {"BOLD_confounds": {}})

        extra_input = {
            "BOLD_confounds": {"data": "wrong"},
        }
        msg = "must be a pandas dataframe"
        with pytest.raises(ValueError, match=msg):
            confound_remover._validate_data(new_input, extra_input)

        extra_input = {"BOLD_confounds": {"data": pd.DataFrame()}}
        with pytest.raises(ValueError, match="Image time series and"):
            confound_remover._validate_data(new_input, extra_input)

        extra_input = {
            "BOLD_confounds": {"data": input["BOLD_confounds"]["data"]}
        }
        with pytest.raises(ValueError, match="format must be specified"):
            confound_remover._validate_data(new_input, extra_input)

        extra_input = {
            "BOLD_confounds": {
                "data": input["BOLD_confounds"]["data"],
                "format": "wrong",
            }
        }
        with pytest.raises(ValueError, match="Invalid confounds format wrong"):
            confound_remover._validate_data(new_input, extra_input)

        extra_input = {
            "BOLD_confounds": {
                "data": input["BOLD_confounds"]["data"],
                "format": "adhoc",
            }
        }
        with pytest.raises(ValueError, match="variables names mappings"):
            confound_remover._validate_data(new_input, extra_input)

        extra_input = {
            "BOLD_confounds": {
                "data": input["BOLD_confounds"]["data"],
                "format": "adhoc",
                "mappings": {},
            }
        }
        with pytest.raises(ValueError, match="mappings to fmriprep"):
            confound_remover._validate_data(new_input, extra_input)

        extra_input = {
            "BOLD_confounds": {
                "data": input["BOLD_confounds"]["data"],
                "format": "adhoc",
                "mappings": {
                    "fmriprep": {
                        "rot_x": "wrong",
                        "rot_y": "rot_z",
                        "rot_z": "rot_y",
                    }
                },
            }
        }
        with pytest.raises(ValueError, match=r"names: \['wrong'\]"):
            confound_remover._validate_data(new_input, extra_input)

        extra_input = {
            "BOLD_confounds": {
                "data": input["BOLD_confounds"]["data"],
                "format": "adhoc",
                "mappings": {
                    "fmriprep": {
                        "wrong": "rot_x",
                        "rot_y": "rot_z",
                        "rot_z": "rot_y",
                    }
                },
            }
        }
        with pytest.raises(ValueError, match=r"Missing columns: \['wrong'\]"):
            confound_remover._validate_data(new_input, extra_input)

        extra_input = {
            "BOLD_confounds": {
                "data": input["BOLD_confounds"]["data"],
                "format": "adhoc",
                "mappings": {
                    "fmriprep": {
                        "rot_x": "rot_x",
                        "rot_y": "rot_z",
                        "rot_z": "rot_y",
                    }
                },
            }
        }
        confound_remover._validate_data(new_input, extra_input)


def test_fMRIPrepConfoundRemover__remove_confounds() -> None:
    """Test fMRIPrepConfoundRemover remove confounds."""
    confound_remover = fMRIPrepConfoundRemover(
        strategy={"wm_csf": "full"}, spike=0.2
    )
    reader = DefaultDataReader()
    with PartlyCloudyTestingDataGrabber(reduce_confounds=False) as dg:
        input = dg["sub-01"]
        input = reader.fit_transform(input)
        confounds = confound_remover._pick_confounds(input["BOLD_confounds"])
        raw_bold = input["BOLD"]["data"]
        clean_bold = confound_remover._remove_confounds(
            bold_img=raw_bold, confounds_df=confounds
        )
        clean_bold = typing.cast(nib.Nifti1Image, clean_bold)
        # TODO: Find a better way to test functionality here
        assert (
            clean_bold.header.get_zooms()  # type: ignore
            == raw_bold.header.get_zooms()  # type: ignore
        )
        assert clean_bold.get_fdata().shape == raw_bold.get_fdata().shape
    # TODO: Test confound remover with mask, needs #79 to be implemented


def test_fMRIPrepConfoundRemover_preprocess() -> None:
    """Test fMRIPrepConfoundRemover with all confounds present."""

    # need reader for the data
    reader = DefaultDataReader()
    # All strategies full, no spike
    confound_remover = fMRIPrepConfoundRemover()

    with PartlyCloudyTestingDataGrabber(reduce_confounds=False) as dg:
        input = dg["sub-01"]
        input = reader.fit_transform(input)
        orig_bold = input["BOLD"]["data"].get_fdata().copy()
        pre_input = input["BOLD"]
        pre_extra_input = {"BOLD_confounds": input["BOLD_confounds"]}
        key, output = confound_remover.preprocess(pre_input, pre_extra_input)
        trans_bold = output["data"].get_fdata()
        # Transformation is in place
        assert_array_equal(trans_bold, input["BOLD"]["data"].get_fdata())

        # Data should have the same shape
        assert orig_bold.shape == trans_bold.shape

        # but be different
        assert_raises(
            AssertionError, assert_array_equal, orig_bold, trans_bold
        )
        assert key == "BOLD"


def test_fMRIPrepConfoundRemover_fit_transform() -> None:
    """Test fMRIPrepConfoundRemover with all confounds present."""

    # need reader for the data
    reader = DefaultDataReader()
    # All strategies full, no spike
    confound_remover = fMRIPrepConfoundRemover()

    with PartlyCloudyTestingDataGrabber(reduce_confounds=False) as dg:
        input = dg["sub-01"]
        input = reader.fit_transform(input)
        orig_bold = input["BOLD"]["data"].get_fdata().copy()
        output = confound_remover.fit_transform(input)
        trans_bold = output["BOLD"]["data"].get_fdata()
        # Transformation is in place
        assert_array_equal(trans_bold, input["BOLD"]["data"].get_fdata())

        # Data should have the same shape
        assert orig_bold.shape == trans_bold.shape

        # but be different
        assert_raises(
            AssertionError, assert_array_equal, orig_bold, trans_bold
        )

        assert "meta" in output["BOLD"]
        assert "preprocess" in output["BOLD"]["meta"]
        t_meta = output["BOLD"]["meta"]["preprocess"]
        assert t_meta["class"] == "fMRIPrepConfoundRemover"
        # It should have all the default parameters
        assert t_meta["strategy"] == confound_remover.strategy
        assert t_meta["spike"] is None
        assert t_meta["detrend"] is True
        assert t_meta["standardize"] is True
        assert t_meta["low_pass"] is None
        assert t_meta["high_pass"] is None
        assert t_meta["t_r"] is None
        assert t_meta["mask_img"] is None

        assert "dependencies" in output["BOLD"]["meta"]
        dependencies = output["BOLD"]["meta"]["dependencies"]
        assert dependencies == {"numpy", "nilearn"}
