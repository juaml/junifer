"""Provide test for (f)ALFF estimator."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

import time

import pytest
from nibabel import Nifti1Image
from scipy.stats import pearsonr

from junifer.datareader import DefaultDataReader
from junifer.markers.falff.falff_estimator import (
    AmplitudeLowFrequencyFluctuationEstimator,
)
from junifer.pipeline.utils import _check_afni
from junifer.testing.datagrabbers import PartlyCloudyTestingDataGrabber
from junifer.utils import logger


def test_AmplitudeLowFrequencyFluctuationEstimator_cache_python() -> None:
    """Test that the cache works properly when using python."""
    with PartlyCloudyTestingDataGrabber() as dg:
        input = dg["sub-01"]

    input = DefaultDataReader().fit_transform(input)

    estimator = AmplitudeLowFrequencyFluctuationEstimator()
    start_time = time.time()
    alff, falff = estimator.fit_transform(
        use_afni=False,
        input_data=input["BOLD"],
        highpass=0.01,
        lowpass=0.1,
        tr=None,
    )
    first_time = time.time() - start_time
    logger.info(f"ALFF Estimator First time: {first_time}")
    assert isinstance(alff, Nifti1Image)
    assert isinstance(falff, Nifti1Image)
    n_files = len([x for x in estimator.temp_dir_path.glob("*")])
    assert n_files == 0  # no files in python

    # Now fit again, should be faster
    start_time = time.time()
    alff, falff = estimator.fit_transform(
        use_afni=False,
        input_data=input["BOLD"],
        highpass=0.01,
        lowpass=0.1,
        tr=None,
    )
    second_time = time.time() - start_time
    logger.info(f"ALFF Estimator Second time: {second_time}")
    assert second_time < (first_time / 1000)
    n_files = len([x for x in estimator.temp_dir_path.glob("*")])
    assert n_files == 0  # no files in python

    # Now change a parameter, should compute again, without clearing the
    # cache
    start_time = time.time()
    alff, falff = estimator.fit_transform(
        use_afni=False,
        input_data=input["BOLD"],
        highpass=0.01,
        lowpass=0.11,
        tr=None,
    )
    third_time = time.time() - start_time
    logger.info(f"ALFF Estimator Third time: {third_time}")
    assert third_time > (first_time / 10)
    n_files = len([x for x in estimator.temp_dir_path.glob("*")])
    assert n_files == 0  # no files in python

    # Now fit again with the previous params, should be fast
    start_time = time.time()
    alff, falff = estimator.fit_transform(
        use_afni=False,
        input_data=input["BOLD"],
        highpass=0.01,
        lowpass=0.1,
        tr=None,
    )
    fourth = time.time() - start_time
    logger.info(f"ALFF Estimator Fourth time: {fourth}")
    assert fourth < (first_time / 1000)
    n_files = len([x for x in estimator.temp_dir_path.glob("*")])
    assert n_files == 0  # no files in python

    # Now change the data, it should clear the cache
    with PartlyCloudyTestingDataGrabber() as dg:
        input = dg["sub-02"]

    input = DefaultDataReader().fit_transform(input)

    start_time = time.time()
    alff, falff = estimator.fit_transform(
        use_afni=False,
        input_data=input["BOLD"],
        highpass=0.01,
        lowpass=0.1,
        tr=None,
    )
    fifth = time.time() - start_time
    logger.info(f"ALFF Estimator Fifth time: {fifth}")
    assert fifth > (first_time / 10)
    n_files = len([x for x in estimator.temp_dir_path.glob("*")])
    assert n_files == 0  # no files in python


@pytest.mark.skipif(
    _check_afni() is False, reason="requires afni to be in PATH"
)
def test_AmplitudeLowFrequencyFluctuationEstimator_cache_afni() -> None:
    """Test that the cache works properly when using afni."""
    with PartlyCloudyTestingDataGrabber() as dg:
        input = dg["sub-01"]

    input = DefaultDataReader().fit_transform(input)

    estimator = AmplitudeLowFrequencyFluctuationEstimator()
    start_time = time.time()
    alff, falff = estimator.fit_transform(
        use_afni=True,
        input_data=input["BOLD"],
        highpass=0.01,
        lowpass=0.1,
        tr=None,
    )
    first_time = time.time() - start_time
    logger.info(f"ALFF Estimator First time: {first_time}")
    assert isinstance(alff, Nifti1Image)
    assert isinstance(falff, Nifti1Image)
    n_files = len([x for x in estimator.temp_dir_path.glob("*")])
    assert n_files == 3  # input + alff + falff

    # Now fit again, should be faster
    start_time = time.time()
    alff, falff = estimator.fit_transform(
        use_afni=True,
        input_data=input["BOLD"],
        highpass=0.01,
        lowpass=0.1,
        tr=None,
    )
    second_time = time.time() - start_time
    logger.info(f"ALFF Estimator Second time: {second_time}")
    assert second_time < (first_time / 1000)
    n_files = len([x for x in estimator.temp_dir_path.glob("*")])
    assert n_files == 3  # input + alff + falff

    # Now change a parameter, should compute again, without clearing the
    # cache
    start_time = time.time()
    alff, falff = estimator.fit_transform(
        use_afni=True,
        input_data=input["BOLD"],
        highpass=0.01,
        lowpass=0.11,
        tr=None,
    )
    third_time = time.time() - start_time
    logger.info(f"ALFF Estimator Third time: {third_time}")
    assert third_time > (first_time / 10)
    n_files = len([x for x in estimator.temp_dir_path.glob("*")])
    assert n_files == 5  # input + 2 * alff + 2 * falff

    # Now fit again with the previous params, should be fast
    start_time = time.time()
    alff, falff = estimator.fit_transform(
        use_afni=True,
        input_data=input["BOLD"],
        highpass=0.01,
        lowpass=0.1,
        tr=None,
    )
    fourth = time.time() - start_time
    logger.info(f"ALFF Estimator Fourth time: {fourth}")
    assert fourth < (first_time / 1000)
    n_files = len([x for x in estimator.temp_dir_path.glob("*")])
    assert n_files == 5  # input + 2 * alff + 2 * falff

    # Now change the data, it should clear the cache
    with PartlyCloudyTestingDataGrabber() as dg:
        input = dg["sub-02"]

    input = DefaultDataReader().fit_transform(input)

    start_time = time.time()
    alff, falff = estimator.fit_transform(
        use_afni=True,
        input_data=input["BOLD"],
        highpass=0.01,
        lowpass=0.1,
        tr=None,
    )
    fifth = time.time() - start_time
    logger.info(f"ALFF Estimator Fifth time: {fifth}")
    assert fifth > (first_time / 10)
    n_files = len([x for x in estimator.temp_dir_path.glob("*")])
    assert n_files == 3  # input + alff + falff


@pytest.mark.skipif(
    _check_afni() is False, reason="requires afni to be in PATH"
)
def test_AmplitudeLowFrequencyFluctuationEstimator_afni_vs_python() -> None:
    """Test that the cache works properly when using afni."""
    with PartlyCloudyTestingDataGrabber() as dg:
        input = dg["sub-01"]

    input = DefaultDataReader().fit_transform(input)
    estimator = AmplitudeLowFrequencyFluctuationEstimator()

    # Use an arbitrary TR to test the AFNI vs Python implementation
    afni_alff, afni_falff = estimator.fit_transform(
        use_afni=True,
        input_data=input["BOLD"],
        highpass=0.01,
        lowpass=0.1,
        tr=2.5,
    )

    python_alff, python_falff = estimator.fit_transform(
        use_afni=False,
        input_data=input["BOLD"],
        highpass=0.01,
        lowpass=0.1,
        tr=2.5,
    )

    r, _ = pearsonr(
        afni_alff.get_fdata().flatten(), python_alff.get_fdata().flatten()
    )
    assert r > 0.99

    r, _ = pearsonr(
        afni_falff.get_fdata().flatten(), python_falff.get_fdata().flatten()
    )
    assert r > 0.99
