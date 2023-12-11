"""Provide test for (f)ALFF estimator."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

import time
from pathlib import Path

import pytest
from nibabel import Nifti1Image
from scipy.stats import pearsonr

from junifer.datareader import DefaultDataReader
from junifer.markers.falff.falff_estimator import ALFFEstimator
from junifer.pipeline import WorkDirManager
from junifer.pipeline.utils import _check_afni
from junifer.testing.datagrabbers import PartlyCloudyTestingDataGrabber
from junifer.utils import logger


def test_ALFFEstimator_cache_python(tmp_path: Path) -> None:
    """Test that the cache works properly when using python.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    # Get subject from datagrabber
    with PartlyCloudyTestingDataGrabber() as dg:
        subject = dg["sub-01"]
    # Read data for subject
    subject_data = DefaultDataReader().fit_transform(subject)
    # Update workdir to current test's tmp_path
    WorkDirManager().workdir = tmp_path
    # Setup estimator
    estimator = ALFFEstimator()

    # Compute without cache
    start_time = time.time()
    alff, falff, alff_path, falff_path = estimator.fit_transform(
        use_afni=False,
        input_data=subject_data["BOLD"],
        highpass=0.01,
        lowpass=0.1,
        tr=None,
    )
    first_time = time.time() - start_time
    logger.info(f"ALFF Estimator First time: {first_time}")
    assert isinstance(alff, Nifti1Image)
    assert isinstance(falff, Nifti1Image)
    assert isinstance(alff_path, Path)
    assert isinstance(falff_path, Path)

    # Compute again with cache, should be faster
    start_time = time.time()
    alff, falff, _, _ = estimator.fit_transform(
        use_afni=False,
        input_data=subject_data["BOLD"],
        highpass=0.01,
        lowpass=0.1,
        tr=None,
    )
    second_time = time.time() - start_time
    logger.info(f"ALFF Estimator Second time: {second_time}")
    assert second_time < (first_time / 1000)

    # Change a parameter and compute again without cache
    start_time = time.time()
    alff, falff, _, _ = estimator.fit_transform(
        use_afni=False,
        input_data=subject_data["BOLD"],
        highpass=0.01,
        lowpass=0.11,
        tr=None,
    )
    third_time = time.time() - start_time
    logger.info(f"ALFF Estimator Third time: {third_time}")
    assert third_time > (first_time / 10)

    # Compute again with cache, should be faster
    start_time = time.time()
    alff, falff, _, _ = estimator.fit_transform(
        use_afni=False,
        input_data=subject_data["BOLD"],
        highpass=0.01,
        lowpass=0.1,
        tr=None,
    )
    fourth = time.time() - start_time
    logger.info(f"ALFF Estimator Fourth time: {fourth}")
    assert fourth < (first_time / 1000)

    # Change the data and it should clear the cache
    with PartlyCloudyTestingDataGrabber() as dg:
        subject = dg["sub-02"]
    # Read data for new subject
    subject_data = DefaultDataReader().fit_transform(subject)

    start_time = time.time()
    alff, falff, _, _ = estimator.fit_transform(
        use_afni=False,
        input_data=subject_data["BOLD"],
        highpass=0.01,
        lowpass=0.1,
        tr=None,
    )
    fifth = time.time() - start_time
    logger.info(f"ALFF Estimator Fifth time: {fifth}")
    assert fifth > (first_time / 10)


@pytest.mark.skipif(
    _check_afni() is False, reason="requires afni to be in PATH"
)
def test_ALFFEstimator_cache_afni(tmp_path: Path) -> None:
    """Test that the cache works properly when using afni.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    # Get subject from datagrabber
    with PartlyCloudyTestingDataGrabber() as dg:
        subject = dg["sub-01"]
    # Read data for subject
    subject_data = DefaultDataReader().fit_transform(subject)
    # Update workdir to current test's tmp_path
    WorkDirManager().workdir = tmp_path
    # Setup estimator
    estimator = ALFFEstimator()

    # Compute with cache
    start_time = time.time()
    alff, falff, alff_path, falff_path = estimator.fit_transform(
        use_afni=True,
        input_data=subject_data["BOLD"],
        highpass=0.01,
        lowpass=0.1,
        tr=None,
    )
    first_time = time.time() - start_time
    logger.info(f"ALFF Estimator First time: {first_time}")
    assert isinstance(alff, Nifti1Image)
    assert isinstance(falff, Nifti1Image)
    assert isinstance(alff_path, Path)
    assert isinstance(falff_path, Path)
    n_files = len(list(estimator.temp_dir_path.glob("*")))
    assert n_files == 1  # only input file

    # Compute again with cache, should be faster
    start_time = time.time()
    alff, falff, _, _ = estimator.fit_transform(
        use_afni=True,
        input_data=subject_data["BOLD"],
        highpass=0.01,
        lowpass=0.1,
        tr=None,
    )
    second_time = time.time() - start_time
    logger.info(f"ALFF Estimator Second time: {second_time}")
    assert second_time < (first_time / 1000)
    n_files = len(list(estimator.temp_dir_path.glob("*")))
    assert n_files == 1  # only input file

    # Change a parameter and compute again without cache
    start_time = time.time()
    alff, falff, _, _ = estimator.fit_transform(
        use_afni=True,
        input_data=subject_data["BOLD"],
        highpass=0.01,
        lowpass=0.11,
        tr=None,
    )
    third_time = time.time() - start_time
    logger.info(f"ALFF Estimator Third time: {third_time}")
    assert third_time > (first_time / 10)
    n_files = len(list(estimator.temp_dir_path.glob("*")))
    assert n_files == 1  # only input file

    # Compute with cache, should be faster
    start_time = time.time()
    alff, falff, _, _ = estimator.fit_transform(
        use_afni=True,
        input_data=subject_data["BOLD"],
        highpass=0.01,
        lowpass=0.1,
        tr=None,
    )
    fourth = time.time() - start_time
    logger.info(f"ALFF Estimator Fourth time: {fourth}")
    assert fourth < (first_time / 1000)
    n_files = len(list(estimator.temp_dir_path.glob("*")))
    assert n_files == 1  # only input file

    # Change the data and it should clear the cache
    with PartlyCloudyTestingDataGrabber() as dg:
        subject = dg["sub-02"]
    # Read data for new subject
    subject_data = DefaultDataReader().fit_transform(subject)

    start_time = time.time()
    alff, falff, _, _ = estimator.fit_transform(
        use_afni=True,
        input_data=subject_data["BOLD"],
        highpass=0.01,
        lowpass=0.1,
        tr=None,
    )
    fifth = time.time() - start_time
    logger.info(f"ALFF Estimator Fifth time: {fifth}")
    assert fifth > (first_time / 10)
    n_files = len(list(estimator.temp_dir_path.glob("*")))
    assert n_files == 1  # only input file


@pytest.mark.skipif(
    _check_afni() is False, reason="requires afni to be in PATH"
)
def test_ALFFEstimator_afni_vs_python(tmp_path: Path) -> None:
    """Test that the cache works properly when using afni.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    # Get subject from datagrabber
    with PartlyCloudyTestingDataGrabber() as dg:
        subject = dg["sub-01"]
    # Read data for subject
    subject_data = DefaultDataReader().fit_transform(subject)
    # Update workdir to current test's tmp_path
    WorkDirManager().workdir = tmp_path
    # Setup estimator
    estimator = ALFFEstimator()

    # Use an arbitrary TR to test the AFNI vs Python implementation
    afni_alff, afni_falff, _, _ = estimator.fit_transform(
        use_afni=True,
        input_data=subject_data["BOLD"],
        highpass=0.01,
        lowpass=0.1,
        tr=2.5,
    )

    python_alff, python_falff, _, _ = estimator.fit_transform(
        use_afni=False,
        input_data=subject_data["BOLD"],
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
