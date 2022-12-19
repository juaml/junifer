"""Provide tests for ReHo map compute comparison."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import time

import nibabel as nib
import pytest
from scipy.stats import pearsonr

from junifer.datareader.default import DefaultDataReader
from junifer.markers.reho.reho_estimator import ReHoEstimator
from junifer.pipeline.utils import _check_afni
from junifer.testing.datagrabbers import PartlyCloudyTestingDataGrabber
from junifer.utils.logging import logger


def test_reho_estimator_cache_python() -> None:
    """Test that the cache works properly when using Python implementation."""
    # Get subject from datagrabber
    with PartlyCloudyTestingDataGrabber() as dg:
        subject = dg["sub-01"]
    # Read data for subject
    subject_data = DefaultDataReader().fit_transform(subject)
    # Setup estimator
    reho_estimator = ReHoEstimator()

    first_tic = time.time()
    reho_map_without_cache = reho_estimator.fit_transform(
        use_afni=False,
        input_data=subject_data["BOLD"],
        nneigh=27,
    )
    first_toc = time.time()
    logger.info(
        f"ReHo estimator in Python without cache: {first_toc - first_tic}"
    )
    assert isinstance(reho_map_without_cache, nib.Nifti1Image)
    # Count intermediate files
    n_files = len([x for x in reho_estimator.temp_dir_path.glob("*")])
    assert n_files == 0  # no files in python

    # Now fit again, should be faster
    second_tic = time.time()
    reho_map_with_cache = reho_estimator.fit_transform(
        use_afni=False,
        input_data=subject_data["BOLD"],
        nneigh=27,
    )
    second_toc = time.time()
    logger.info(
        f"ReHo estimator in Python with cache: {second_toc - second_tic}"
    )
    assert isinstance(reho_map_with_cache, nib.Nifti1Image)
    # Check that cache is being used
    assert (second_toc - second_tic) < ((first_toc - first_tic) / 1000)
    # Count intermediate files
    n_files = len([x for x in reho_estimator.temp_dir_path.glob("*")])
    assert n_files == 0  # no files in python

    # Now change a parameter, should compute again, without clearing the
    # cache
    third_tic = time.time()
    reho_map_with_partial_cache = reho_estimator.fit_transform(
        use_afni=False,
        input_data=subject_data["BOLD"],
        nneigh=125,
    )
    third_toc = time.time()
    logger.info(
        f"ReHo estimator in Python with partial cache: {third_toc - third_tic}"
    )
    assert isinstance(reho_map_with_partial_cache, nib.Nifti1Image)
    # Should require more time
    assert (third_toc - third_tic) > ((first_toc - first_tic) / 10)
    # Count intermediate files
    n_files = len([x for x in reho_estimator.temp_dir_path.glob("*")])
    assert n_files == 0  # no files in python

    # Now fit again with the previous params, should be fast
    fourth_tic = time.time()
    reho_map_with_new_cache = reho_estimator.fit_transform(
        use_afni=False,
        input_data=subject_data["BOLD"],
        nneigh=125,
    )
    fourth_toc = time.time()
    logger.info(
        f"ReHo estimator in Python with new cache: {fourth_toc - fourth_tic}"
    )
    assert isinstance(reho_map_with_new_cache, nib.Nifti1Image)
    # Should require less time
    assert (fourth_toc - fourth_tic) < ((first_toc - first_tic) / 1000)
    # Count intermediate files
    n_files = len([x for x in reho_estimator.temp_dir_path.glob("*")])
    assert n_files == 0  # no files in python

    # Now change the data, it should clear the cache
    with PartlyCloudyTestingDataGrabber() as dg:
        subject = dg["sub-02"]
    # Read data for new subject
    subject_data = DefaultDataReader().fit_transform(subject)

    fifth_tic = time.time()
    reho_map_with_different_cache = reho_estimator.fit_transform(
        use_afni=False,
        input_data=subject_data["BOLD"],
        nneigh=27,
    )
    fifth_toc = time.time()
    logger.info(
        "ReHo estimator in Python with different cache: "
        f"{fifth_toc - fifth_tic}"
    )
    assert isinstance(reho_map_with_different_cache, nib.Nifti1Image)
    # Should take less time
    assert (fifth_toc - fifth_tic) > ((first_toc - first_tic) / 10)
    # Count intermediate files
    n_files = len([x for x in reho_estimator.temp_dir_path.glob("*")])
    assert n_files == 0  # no files in python


@pytest.mark.skipif(
    _check_afni() is False, reason="requires afni to be in PATH"
)
def test_reho_estimator_cache_afni() -> None:
    """Test that the cache works properly when using afni."""
    # Get subject from datagrabber
    with PartlyCloudyTestingDataGrabber() as dg:
        subject = dg["sub-01"]
    # Read data for subject
    subject_data = DefaultDataReader().fit_transform(subject)
    # Setup estimator
    reho_estimator = ReHoEstimator()

    first_tic = time.time()
    reho_map_without_cache = reho_estimator.fit_transform(
        use_afni=True,
        input_data=subject_data["BOLD"],
        nneigh=19,
    )
    first_toc = time.time()
    logger.info(
        f"ReHo estimator in AFNI without cache: {first_toc - first_tic}"
    )
    assert isinstance(reho_map_without_cache, nib.Nifti1Image)
    # Count intermediate files
    n_files = len([x for x in reho_estimator.temp_dir_path.glob("*")])
    assert n_files == 2  # input + reho

    # Now fit again, should be faster
    second_tic = time.time()
    reho_map_with_cache = reho_estimator.fit_transform(
        use_afni=True,
        input_data=subject_data["BOLD"],
        nneigh=19,
    )
    second_toc = time.time()
    logger.info(
        f"ReHo estimator in AFNI with cache: {second_toc - second_tic}"
    )
    assert isinstance(reho_map_with_cache, nib.Nifti1Image)
    assert (second_toc - second_tic) < ((first_toc - first_tic) / 1000)
    # Count intermediate files
    n_files = len([x for x in reho_estimator.temp_dir_path.glob("*")])
    assert n_files == 2  # input + reho

    # Now change a parameter, should compute again, without clearing the
    # cache
    third_tic = time.time()
    reho_map_with_partial_cache = reho_estimator.fit_transform(
        use_afni=True,
        input_data=subject_data["BOLD"],
        nneigh=27,
    )
    third_toc = time.time()
    logger.info(
        f"ReHo estimator in AFNI with partial cache: {third_toc - third_tic}"
    )
    assert isinstance(reho_map_with_partial_cache, nib.Nifti1Image)
    # Should require more time
    assert (third_toc - third_tic) > ((first_toc - first_tic) / 10)
    # Count intermediate files
    n_files = len([x for x in reho_estimator.temp_dir_path.glob("*")])
    assert n_files == 3  # input + 2 * reho

    # Now fit again with the previous params, should be fast
    fourth_tic = time.time()
    reho_map_with_new_cache = reho_estimator.fit_transform(
        use_afni=True,
        input_data=subject_data["BOLD"],
        nneigh=27,
    )
    fourth_toc = time.time()
    logger.info(
        f"ReHo estimator in AFNI with new cache: {fourth_toc - fourth_tic}"
    )
    assert isinstance(reho_map_with_new_cache, nib.Nifti1Image)
    # Should require less time
    assert (fourth_toc - fourth_tic) < ((first_toc - first_tic) / 1000)
    n_files = len([x for x in reho_estimator.temp_dir_path.glob("*")])
    assert n_files == 3  # input + 2 * reho

    # Now change the data, it should clear the cache
    with PartlyCloudyTestingDataGrabber() as dg:
        subject = dg["sub-02"]
    # Read data for new subject
    subject_data = DefaultDataReader().fit_transform(subject)

    fifth_tic = time.time()
    reho_map_with_different_cache = reho_estimator.fit_transform(
        use_afni=True,
        input_data=subject_data["BOLD"],
        nneigh=27,
    )
    fifth_toc = time.time()
    logger.info(
        f"ReHo estimator in AFNI with different cache: {fifth_toc - fifth_tic}"
    )
    assert isinstance(reho_map_with_different_cache, nib.Nifti1Image)
    # Should take less time
    assert (fifth_toc - fifth_tic) > ((first_toc - first_tic) / 10)
    # Count intermediate files
    n_files = len([x for x in reho_estimator.temp_dir_path.glob("*")])
    assert n_files == 2  # input + reho


@pytest.mark.skipif(
    _check_afni() is False, reason="requires afni to be in PATH"
)
def test_reho_estimator_afni_vs_python() -> None:
    """Compare afni and Python implementations."""
    # Get subject from datagrabber
    with PartlyCloudyTestingDataGrabber() as dg:
        subject = dg["sub-01"]
    # Read data for subject
    subject_data = DefaultDataReader().fit_transform(subject)
    # Setup estimator
    reho_estimator = ReHoEstimator()

    # Compare using 27 neighbours
    reho_map_afni = reho_estimator.fit_transform(
        use_afni=True,
        input_data=subject_data["BOLD"],
        nneigh=27,
    )
    reho_map_python = reho_estimator.fit_transform(
        use_afni=False,
        input_data=subject_data["BOLD"],
        nneigh=27,
    )

    # Calculate Pearson correlation coefficient
    r, _ = pearsonr(
        reho_map_afni.get_fdata().flatten(),
        reho_map_python.get_fdata().flatten(),
    )
    # Assert good correlation
    assert r > 0.70
