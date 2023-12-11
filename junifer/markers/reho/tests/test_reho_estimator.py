"""Provide tests for ReHo map compute comparison."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import time
from pathlib import Path

import nibabel as nib
import pytest
from scipy.stats import pearsonr

from junifer.datareader.default import DefaultDataReader
from junifer.markers.reho.reho_estimator import ReHoEstimator
from junifer.pipeline import WorkDirManager
from junifer.pipeline.utils import _check_afni
from junifer.testing.datagrabbers import PartlyCloudyTestingDataGrabber
from junifer.utils.logging import logger


def test_reho_estimator_cache_python(tmp_path: Path) -> None:
    """Test that the cache works properly when using Python implementation.

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
    reho_estimator = ReHoEstimator()

    # Compute without cache
    first_tic = time.time()
    (
        reho_map_without_cache,
        reho_map_without_cache_path,
    ) = reho_estimator.fit_transform(
        use_afni=False,
        input_data=subject_data["BOLD"],
        nneigh=27,
    )
    first_toc = time.time()
    logger.info(
        f"ReHo estimator in Python without cache: {first_toc - first_tic}"
    )
    assert isinstance(reho_map_without_cache, nib.Nifti1Image)
    assert isinstance(reho_map_without_cache_path, Path)

    # Compute again with cache, should be faster
    second_tic = time.time()
    (
        reho_map_with_cache,
        reho_map_with_cache_path,
    ) = reho_estimator.fit_transform(
        use_afni=False,
        input_data=subject_data["BOLD"],
        nneigh=27,
    )
    second_toc = time.time()
    logger.info(
        f"ReHo estimator in Python with cache: {second_toc - second_tic}"
    )
    assert isinstance(reho_map_with_cache, nib.Nifti1Image)
    assert isinstance(reho_map_with_cache_path, Path)
    # Check that cache is being used
    assert (second_toc - second_tic) < ((first_toc - first_tic) / 1000)

    # Change a parameter and compute again without cache
    third_tic = time.time()
    (
        reho_map_with_partial_cache,
        reho_map_with_partial_cache_path,
    ) = reho_estimator.fit_transform(
        use_afni=False,
        input_data=subject_data["BOLD"],
        nneigh=125,
    )
    third_toc = time.time()
    logger.info(
        f"ReHo estimator in Python with partial cache: {third_toc - third_tic}"
    )
    assert isinstance(reho_map_with_partial_cache, nib.Nifti1Image)
    assert isinstance(reho_map_with_partial_cache_path, Path)
    # Should require more time
    assert (third_toc - third_tic) > ((first_toc - first_tic) / 10)

    # Compute again with cache, should be faster
    fourth_tic = time.time()
    (
        reho_map_with_new_cache,
        reho_map_with_new_cache_path,
    ) = reho_estimator.fit_transform(
        use_afni=False,
        input_data=subject_data["BOLD"],
        nneigh=125,
    )
    fourth_toc = time.time()
    logger.info(
        f"ReHo estimator in Python with new cache: {fourth_toc - fourth_tic}"
    )
    assert isinstance(reho_map_with_new_cache, nib.Nifti1Image)
    assert isinstance(reho_map_with_new_cache_path, Path)
    # Should require less time
    assert (fourth_toc - fourth_tic) < ((first_toc - first_tic) / 1000)

    # Change the data and it should clear the cache
    with PartlyCloudyTestingDataGrabber() as dg:
        subject = dg["sub-02"]
    # Read data for new subject
    subject_data = DefaultDataReader().fit_transform(subject)

    fifth_tic = time.time()
    (
        reho_map_with_different_cache,
        reho_map_with_different_cache_path,
    ) = reho_estimator.fit_transform(
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
    assert isinstance(reho_map_with_different_cache_path, Path)
    # Should take less time
    assert (fifth_toc - fifth_tic) > ((first_toc - first_tic) / 10)


@pytest.mark.skipif(
    _check_afni() is False, reason="requires afni to be in PATH"
)
def test_reho_estimator_cache_afni(tmp_path: Path) -> None:
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
    reho_estimator = ReHoEstimator()

    # Compute without cache
    first_tic = time.time()
    (
        reho_map_without_cache,
        reho_map_without_cache_path,
    ) = reho_estimator.fit_transform(
        use_afni=True,
        input_data=subject_data["BOLD"],
        nneigh=19,
    )
    first_toc = time.time()
    logger.info(
        f"ReHo estimator in AFNI without cache: {first_toc - first_tic}"
    )
    assert isinstance(reho_map_without_cache, nib.Nifti1Image)
    assert isinstance(reho_map_without_cache_path, Path)
    # Count intermediate files
    n_files = len(list(reho_estimator.temp_dir_path.glob("*")))
    assert n_files == 1  # only input file

    # Compute again with cache, should be faster
    second_tic = time.time()
    (
        reho_map_with_cache,
        reho_map_with_cache_path,
    ) = reho_estimator.fit_transform(
        use_afni=True,
        input_data=subject_data["BOLD"],
        nneigh=19,
    )
    second_toc = time.time()
    logger.info(
        f"ReHo estimator in AFNI with cache: {second_toc - second_tic}"
    )
    assert isinstance(reho_map_with_cache, nib.Nifti1Image)
    assert isinstance(reho_map_with_cache_path, Path)
    assert (second_toc - second_tic) < ((first_toc - first_tic) / 1000)
    # Count intermediate files
    n_files = len(list(reho_estimator.temp_dir_path.glob("*")))
    assert n_files == 1  # only input file

    # Change a parameter and compute again without cache
    third_tic = time.time()
    (
        reho_map_with_partial_cache,
        reho_map_with_partial_cache_path,
    ) = reho_estimator.fit_transform(
        use_afni=True,
        input_data=subject_data["BOLD"],
        nneigh=27,
    )
    third_toc = time.time()
    logger.info(
        f"ReHo estimator in AFNI with partial cache: {third_toc - third_tic}"
    )
    assert isinstance(reho_map_with_partial_cache, nib.Nifti1Image)
    assert isinstance(reho_map_with_partial_cache_path, Path)
    # Should require more time
    assert (third_toc - third_tic) > ((first_toc - first_tic) / 10)
    # Count intermediate files
    n_files = len(list(reho_estimator.temp_dir_path.glob("*")))
    assert n_files == 1  # only input file

    # Compute with cache, should be faster
    fourth_tic = time.time()
    (
        reho_map_with_new_cache,
        reho_map_with_new_cache_path,
    ) = reho_estimator.fit_transform(
        use_afni=True,
        input_data=subject_data["BOLD"],
        nneigh=27,
    )
    fourth_toc = time.time()
    logger.info(
        f"ReHo estimator in AFNI with new cache: {fourth_toc - fourth_tic}"
    )
    assert isinstance(reho_map_with_new_cache, nib.Nifti1Image)
    assert isinstance(reho_map_with_new_cache_path, Path)
    # Should require less time
    assert (fourth_toc - fourth_tic) < ((first_toc - first_tic) / 1000)
    n_files = len(list(reho_estimator.temp_dir_path.glob("*")))
    assert n_files == 1  # only input file

    # Change the data and it should clear the cache
    with PartlyCloudyTestingDataGrabber() as dg:
        subject = dg["sub-02"]
    # Read data for new subject
    subject_data = DefaultDataReader().fit_transform(subject)

    fifth_tic = time.time()
    (
        reho_map_with_different_cache,
        reho_map_with_different_cache_path,
    ) = reho_estimator.fit_transform(
        use_afni=True,
        input_data=subject_data["BOLD"],
        nneigh=27,
    )
    fifth_toc = time.time()
    logger.info(
        f"ReHo estimator in AFNI with different cache: {fifth_toc - fifth_tic}"
    )
    assert isinstance(reho_map_with_different_cache, nib.Nifti1Image)
    assert isinstance(reho_map_with_different_cache_path, Path)
    # Should take less time
    assert (fifth_toc - fifth_tic) > ((first_toc - first_tic) / 10)
    # Count intermediate files
    n_files = len(list(reho_estimator.temp_dir_path.glob("*")))
    assert n_files == 1  # only input file


@pytest.mark.skipif(
    _check_afni() is False, reason="requires afni to be in PATH"
)
def test_reho_estimator_afni_vs_python(tmp_path: Path) -> None:
    """Compare afni and Python implementations.

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
    reho_estimator = ReHoEstimator()

    # Compare using 27 neighbours
    reho_map_afni, _ = reho_estimator.fit_transform(
        use_afni=True,
        input_data=subject_data["BOLD"],
        nneigh=27,
    )
    reho_map_python, _ = reho_estimator.fit_transform(
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
