"""Provide tests for fMRIPrepConfoundRemover."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL


import numpy as np
import pandas as pd
import pytest
from nilearn._utils.exceptions import DimensionError
from nilearn.interfaces.fmriprep.load_confounds_utils import prepare_output
from numpy.testing import assert_array_equal, assert_raises
from pandas.testing import assert_frame_equal

from junifer.datareader import DefaultDataReader
from junifer.preprocess.confounds import fMRIPrepConfoundRemover
from junifer.testing import get_testing_data
from junifer.testing.datagrabbers import (
    OasisVBMTestingDataGrabber,
    PartlyCloudyTestingDataGrabber,
    SPMAuditoryTestingDataGrabber,
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


@pytest.mark.parametrize(
    "input_",
    [
        ["BOLD"],
        ["T1w", "BOLD"],
    ],
)
def test_fMRIPrepConfoundRemover_validate_input(input_: list[str]) -> None:
    """Test fMRIPrepConfoundRemover validate_input.

    Parameters
    ----------
    input_ : list of str
        The input data types.

    """
    confound_remover = fMRIPrepConfoundRemover()
    confound_remover.validate_input(input_)


def test_fMRIPrepConfoundRemover_get_valid_inputs() -> None:
    """Test fMRIPrepConfoundRemover get_valid_inputs."""
    confound_remover = fMRIPrepConfoundRemover()
    assert confound_remover.get_valid_inputs() == ["BOLD"]


def test_fMRIPrepConfoundRemover_get_output_type() -> None:
    """Test fMRIPrepConfoundRemover get_output_type."""
    confound_remover = fMRIPrepConfoundRemover()
    # Confound remover works in place
    assert confound_remover.get_output_type("BOLD") == "BOLD"


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
    mappings = dict(zip(adhoc_names, fmriprep_names))
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
        columns=[*var_names, "framewise_displacement"],
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
    with pytest.raises(RuntimeError, match=msg):
        confound_remover._process_fmriprep_spec({"data": confounds_df})

    var_names = ["csf", "white_matter"]
    confounds_df = pd.DataFrame(
        np.random.randn(7, len(var_names)), columns=var_names
    )

    msg = r"Missing framewise_displacement"
    with pytest.raises(RuntimeError, match=msg):
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
    mappings = dict(zip(adhoc_names, fmriprep_names))
    input = {
        "mappings": {"fmriprep": mappings},
        "data": adhoc_df,
        "format": "adhoc",
    }

    out = confound_remover._pick_confounds(input)
    assert set(out.columns) == set(fmriprep_all_vars)


def test_fMRIPRepConfoundRemover__pick_confounds_fmriprep() -> None:
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
        out1 = confound_remover._pick_confounds(input["BOLD"]["confounds"])
        assert set(out1.columns) == {*fmriprep_all_vars, "spike"}

    with PartlyCloudyTestingDataGrabber(reduce_confounds=False) as dg:
        input = dg["sub-01"]
        input = reader.fit_transform(input)
        out2 = confound_remover._pick_confounds(input["BOLD"]["confounds"])
        assert set(out2.columns) == {*fmriprep_all_vars, "spike"}

    assert_frame_equal(out1, out2)


def test_fMRIPRepConfoundRemover__pick_confounds_fmriprep_compute() -> None:
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


@pytest.mark.parametrize(
    "preprocessor",
    [
        fMRIPrepConfoundRemover(
            std_dvars_threshold=1.5,
        ),
        fMRIPrepConfoundRemover(
            fd_threshold=0.5,
        ),
    ],
)
def test_fMRIPrepConfoundRemover__get_scrub_regressors_errors(
    preprocessor: type,
) -> None:
    """Test fMRIPrepConfoundRemover scrub regressors errors.

    Parameters
    ----------
    preprocessor : object
        The parametrized preprocessor.

    """
    with pytest.raises(RuntimeError, match="Invalid confounds file."):
        preprocessor._get_scrub_regressors(pd.DataFrame({"a": [1, 2]}))


def test_fMRIPrepConfoundRemover__validate_data() -> None:
    """Test fMRIPrepConfoundRemover validate data."""
    confound_remover = fMRIPrepConfoundRemover(strategy={"wm_csf": "full"})
    # Check correct data type
    with OasisVBMTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        vbm = element_data["VBM_GM"]
        with pytest.raises(
            DimensionError, match="incompatible dimensionality"
        ):
            confound_remover._validate_data(vbm)
    # Check missing nested type in correct data type
    with SPMAuditoryTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        bold = element_data["BOLD"]
        # Test confound type
        with pytest.raises(
            ValueError, match="`BOLD.confounds` data type not provided"
        ):
            confound_remover._validate_data(bold)
        # Test confound data
        bold["confounds"] = {}
        with pytest.raises(
            ValueError, match="`BOLD.confounds.data` not provided"
        ):
            confound_remover._validate_data(bold)
        # Test confound data is valid type
        bold["confounds"] = {"data": None}
        with pytest.raises(ValueError, match="must be a `pandas.DataFrame`"):
            confound_remover._validate_data(bold)
        # Test confound data dimension mismatch with BOLD
        bold["confounds"] = {"data": pd.DataFrame()}
        with pytest.raises(ValueError, match="Image time series and"):
            confound_remover._validate_data(bold)
    # Check nested type variations
    with PartlyCloudyTestingDataGrabber(reduce_confounds=False) as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        # Test format
        modified_bold = {
            "data": element_data["BOLD"]["data"],
            "confounds": {
                "data": element_data["BOLD"]["confounds"]["data"],
                "format": "adhoc",
            },
        }
        # Test incorrect format
        modified_bold["confounds"].update({"format": "wrong"})
        with pytest.raises(ValueError, match="Invalid confounds format"):
            confound_remover._validate_data(modified_bold)
        # Test missing mappings for adhoc
        modified_bold["confounds"].update({"format": "adhoc"})
        with pytest.raises(
            ValueError, match="`BOLD.confounds.mappings` need to be set"
        ):
            confound_remover._validate_data(modified_bold)
        # Test missing fmriprep mappings for adhoc
        modified_bold["confounds"].update({"mappings": {}})
        with pytest.raises(
            ValueError,
            match="`BOLD.confounds.mappings.fmriprep` need to be set",
        ):
            confound_remover._validate_data(modified_bold)
        # Test incorrect fmriprep mappings for adhoc
        modified_bold["confounds"].update(
            {
                "mappings": {
                    "fmriprep": {
                        "rot_x": "wrong",
                        "rot_y": "rot_z",
                        "rot_z": "rot_y",
                    },
                }
            }
        )
        with pytest.raises(ValueError, match=r"names: \['wrong'\]"):
            confound_remover._validate_data(modified_bold)
        # Test missing fmriprep mappings for adhoc
        modified_bold["confounds"].update(
            {
                "mappings": {
                    "fmriprep": {
                        "wrong": "rot_x",
                        "rot_y": "rot_z",
                        "rot_z": "rot_y",
                    },
                }
            }
        )
        with pytest.raises(ValueError, match=r"Missing columns: \['wrong'\]"):
            confound_remover._validate_data(modified_bold)
        # Test correct adhoc format
        modified_bold["confounds"].update(
            {
                "mappings": {
                    "fmriprep": {
                        "rot_x": "rot_x",
                        "rot_y": "rot_z",
                        "rot_z": "rot_y",
                    },
                }
            }
        )
        confound_remover._validate_data(modified_bold)


def test_fMRIPrepConfoundRemover_preprocess() -> None:
    """Test fMRIPrepConfoundRemover with all confounds present."""
    # All strategies full, no spike
    confound_remover = fMRIPrepConfoundRemover()

    with PartlyCloudyTestingDataGrabber(reduce_confounds=False) as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        orig_bold = element_data["BOLD"]["data"].get_fdata().copy()
        pre_input = element_data["BOLD"]
        pre_extra_input = {
            "BOLD": {"confounds": element_data["BOLD"]["confounds"]}
        }
        output, _ = confound_remover.preprocess(pre_input, pre_extra_input)
        trans_bold = output["data"].get_fdata()
        # Transformation is in place
        assert_array_equal(
            trans_bold, element_data["BOLD"]["data"].get_fdata()
        )

        # Data should have the same shape
        assert orig_bold.shape == trans_bold.shape

        # but be different
        assert_raises(
            AssertionError, assert_array_equal, orig_bold, trans_bold
        )


def test_fMRIPrepConfoundRemover_fit_transform() -> None:
    """Test fMRIPrepConfoundRemover with all confounds present."""
    # All strategies full, no spike
    confound_remover = fMRIPrepConfoundRemover()

    with PartlyCloudyTestingDataGrabber(reduce_confounds=False) as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        # Get original data
        input_img = element_data["BOLD"]["data"]
        input_bold = input_img.get_fdata().copy()
        input_tr = input_img.header.get_zooms()[3]
        # Fit-transform
        output = confound_remover.fit_transform(element_data)
        output_img = output["BOLD"]["data"]
        output_bold = output_img.get_fdata()
        output_tr = output_img.header.get_zooms()[3]

        # Transformation is in place
        assert_array_equal(
            output_bold, element_data["BOLD"]["data"].get_fdata()
        )

        # Data should have the same shape
        assert input_bold.shape == output_bold.shape

        # but be different
        assert_raises(
            AssertionError, assert_array_equal, input_bold, output_bold
        )

        # Check t_r
        assert input_tr == output_tr

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
        assert t_meta["masks"] is None

        assert "mask" not in output["BOLD"]

        assert "dependencies" in output["BOLD"]["meta"]
        dependencies = output["BOLD"]["meta"]["dependencies"]
        assert dependencies == {"numpy", "nilearn"}


def test_fMRIPrepConfoundRemover_fit_transform_masks() -> None:
    """Test fMRIPrepConfoundRemover with all confounds present."""
    # All strategies full, no spike
    confound_remover = fMRIPrepConfoundRemover(
        masks={"compute_brain_mask": {"threshold": 0.2}}
    )

    with PartlyCloudyTestingDataGrabber(reduce_confounds=False) as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        # Get original data
        input_img = element_data["BOLD"]["data"]
        input_bold = input_img.get_fdata().copy()
        input_tr = input_img.header.get_zooms()[3]
        # Fit-transform
        output = confound_remover.fit_transform(element_data)
        output_img = output["BOLD"]["data"]
        output_bold = output_img.get_fdata()
        output_tr = output_img.header.get_zooms()[3]

        # Transformation is in place
        assert_array_equal(
            output_bold, element_data["BOLD"]["data"].get_fdata()
        )

        # Data should have the same shape
        assert input_bold.shape == output_bold.shape

        # but be different
        assert_raises(
            AssertionError, assert_array_equal, input_bold, output_bold
        )

        # Check t_r
        assert input_tr == output_tr

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
        assert isinstance(t_meta["masks"], dict)
        assert t_meta["masks"] is not None
        assert len(t_meta["masks"]) == 1
        assert "compute_brain_mask" in t_meta["masks"]
        assert len(t_meta["masks"]["compute_brain_mask"]) == 1
        assert "threshold" in t_meta["masks"]["compute_brain_mask"]
        assert t_meta["masks"]["compute_brain_mask"]["threshold"] == 0.2

        assert "mask" in output["BOLD"]

        assert "dependencies" in output["BOLD"]["meta"]
        dependencies = output["BOLD"]["meta"]["dependencies"]
        assert dependencies == {"numpy", "nilearn"}


def test_fMRIPrepConfoundRemover_scrubbing() -> None:
    """Test fMRIPrepConfoundRemover with scrubbing."""
    confound_remover = fMRIPrepConfoundRemover(
        strategy={
            "motion": "full",
            "wm_csf": "full",
            "global_signal": "full",
            "scrubbing": True,
        },
    )

    with PartlyCloudyTestingDataGrabber(reduce_confounds=False) as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        orig_bold = element_data["BOLD"]["data"].get_fdata().copy()
        orig_confounds = element_data["BOLD"]["confounds"].copy()
        pre_input = element_data["BOLD"]
        pre_extra_input = {
            "BOLD": {"confounds": element_data["BOLD"]["confounds"]}
        }
        output, _ = confound_remover.preprocess(pre_input, pre_extra_input)
        trans_bold = output["data"].get_fdata()
        # Transformation is in place
        assert_array_equal(
            trans_bold, element_data["BOLD"]["data"].get_fdata()
        )

        # Data should have different shape
        assert_raises(
            AssertionError,
            assert_array_equal,
            orig_bold.shape,
            trans_bold.shape,
        )
        # and be different
        assert_raises(
            AssertionError, assert_array_equal, orig_bold, trans_bold
        )

        # Check scrubbing process
        # Should be at the start
        confounds_df = confound_remover._pick_confounds(orig_confounds)
        assert confounds_df.shape == (168, 36)
        # Should have 4 motion outliers based on threshold
        motion_outline_regressors = confound_remover._get_scrub_regressors(
            orig_confounds["data"]
        )
        assert motion_outline_regressors.shape == (168, 4)
        # Add regressors to confounds
        concat_confounds_df = pd.concat(
            [confounds_df, motion_outline_regressors], axis=1
        )
        assert concat_confounds_df.shape == (168, 40)
        # Get sample mask and correct confounds
        sample_mask, final_confounds_df = prepare_output(
            confounds=concat_confounds_df, demean=False
        )
        assert not confounds_df.equals(final_confounds_df)
        assert sample_mask.shape == (164,)
        assert not (np.isin([91, 92, 93, 113], sample_mask)).all()
