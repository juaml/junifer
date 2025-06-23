"""Provide tests for read-and-transform."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import logging
from pathlib import Path

import numpy as np
import pytest

from junifer.onthefly import read_transform
from junifer.storage.hdf5 import HDF5FeatureStorage


@pytest.fixture
def vector_storage(tmp_path: Path) -> HDF5FeatureStorage:
    """Return a HDF5FeatureStorage with vector data.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    storage = HDF5FeatureStorage(tmp_path / "vector_store.hdf5")
    storage.store(
        kind="vector",
        meta={
            "element": {"subject": "test"},
            "dependencies": [],
            "marker": {"name": "vector"},
            "type": "BOLD",
        },
        data=np.arange(2).reshape(1, 2),
        col_names=["f1", "f2"],
    )
    return storage


@pytest.fixture
def matrix_storage(tmp_path: Path) -> HDF5FeatureStorage:
    """Return a HDF5FeatureStorage with matrix data.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    storage = HDF5FeatureStorage(tmp_path / "matrix_store.hdf5")
    storage.store(
        kind="matrix",
        meta={
            "element": {"subject": "test"},
            "dependencies": [],
            "marker": {"name": "matrix"},
            "type": "BOLD",
        },
        data=np.arange(4).reshape(2, 2),
        col_names=["f1", "f2"],
        row_names=["g1", "g2"],
    )
    return storage


@pytest.fixture
def matrix_storage_with_nan(tmp_path: Path) -> HDF5FeatureStorage:
    """Return a HDF5FeatureStorage with matrix data.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    storage = HDF5FeatureStorage(tmp_path / "matrix_store_nan.hdf5")
    data = np.arange(36).reshape(3, 3, 4).astype(float)
    data[1, 1, 2] = np.nan
    data[1, 2, 2] = np.nan
    for i in range(4):
        storage.store(
            kind="matrix",
            meta={
                "element": {"subject": f"test{i + 1}"},
                "dependencies": [],
                "marker": {"name": "matrix"},
                "type": "BOLD",
            },
            data=data[:, :, i],
            col_names=["f1", "f2", "f3"],
            row_names=["g1", "g2", "g3"],
        )
    return storage


def test_incorrect_package(matrix_storage: HDF5FeatureStorage) -> None:
    """Test error check for incorrect package name.

    Parameters
    ----------
    matrix_storage : HDF5FeatureStorage
        The HDF5FeatureStorage with matrix data, as fixture.

    """
    with pytest.raises(ValueError, match="Unknown package"):
        read_transform(
            storage=matrix_storage,  # type: ignore
            feature_name="BOLD_matrix",
            transform="godspeed_makemake",
        )


def test_incorrect_data_kind(vector_storage: HDF5FeatureStorage) -> None:
    """Test error check for incorrect data kind.

    Parameters
    ----------
    vector_storage : HDF5FeatureStorage
        The HDF5FeatureStorage with vector data, as fixture.

    """
    with pytest.raises(RuntimeError, match="not valid data kind"):
        read_transform(
            storage=vector_storage,  # type: ignore
            feature_name="BOLD_vector",
            transform="bctpy_gonggong",
        )


def test_untested_bctpy_function(matrix_storage: HDF5FeatureStorage) -> None:
    """Test warning check for untested function of bctpy.

    Parameters
    ----------
    matrix_storage : HDF5FeatureStorage
        The HDF5FeatureStorage with matrix data, as fixture.

    """
    # Skip test if import fails
    pytest.importorskip("bct")

    with pytest.raises(ValueError):
        with pytest.warns(RuntimeWarning, match="You are about to use"):
            read_transform(
                storage=matrix_storage,  # type: ignore
                feature_name="BOLD_matrix",
                transform="bctpy_distance_bin",
            )


def test_incorrect_bctpy_function(matrix_storage: HDF5FeatureStorage) -> None:
    """Test error check for incorrect function of bctpy.

    Parameters
    ----------
    matrix_storage : HDF5FeatureStorage
        The HDF5FeatureStorage with matrix data, as fixture.

    """
    # Skip test if import fails
    pytest.importorskip("bct")

    with pytest.raises(AttributeError, match="has no attribute"):
        read_transform(
            storage=matrix_storage,  # type: ignore
            feature_name="BOLD_matrix",
            transform="bctpy_haumea",
        )


@pytest.mark.parametrize(
    "func",
    (
        "degrees_und",
        "strengths_und",
        "clustering_coef_wu",
        "eigenvector_centrality_und",
    ),
)
def test_bctpy_function(
    matrix_storage: HDF5FeatureStorage,
    caplog: pytest.LogCaptureFixture,
    func: str,
) -> None:
    """Test working function of bctpy.

    Parameters
    ----------
    matrix_storage : HDF5FeatureStorage
        The HDF5FeatureStorage with matrix data, as fixture.
    caplog : pytest.LogCaptureFixture
        The pytest.LogCaptureFixture object.
    func : str
        The function to test.

    """
    # Skip test if import fails
    pytest.importorskip("bct")

    with caplog.at_level(logging.DEBUG):
        read_transform(
            storage=matrix_storage,  # type: ignore
            feature_name="BOLD_matrix",
            transform=f"bctpy_{func}",
        )
        assert "Computing" in caplog.text
        assert "Generating" in caplog.text


@pytest.mark.parametrize(
    "nan_policy, error_msg",
    [
        ("drop_element", None),
        ("drop_rows", "square"),
        ("drop_columns", "square"),
        ("drop_symmetric", None),
        ("bypass", "NaNs"),
        ("wrong", "Unknown"),
    ],
)
def test_bctpy_nans(
    matrix_storage_with_nan: HDF5FeatureStorage,
    caplog: pytest.LogCaptureFixture,
    nan_policy: str,
    error_msg: str,
) -> None:
    """Test working function of bctpy.

    Parameters
    ----------
    matrix_storage_with_nan : HDF5FeatureStorage
        The HDF5FeatureStorage with matrix data, as fixture.
    caplog : pytest.LogCaptureFixture
        The pytest.LogCaptureFixture object.
    nan_policy : str
        The NAN policy to test.
    error_msg : str
        The expected error message snippet. If None, no error should be raised.

    """
    # Skip test if import fails
    pytest.importorskip("bct")

    with caplog.at_level(logging.DEBUG):
        if error_msg is None:
            read_transform(
                storage=matrix_storage_with_nan,  # type: ignore
                feature_name="BOLD_matrix",
                transform="bctpy_eigenvector_centrality_und",
                nan_policy=nan_policy,
            )
            assert "Computing" in caplog.text
            assert "Generating" in caplog.text
        else:
            with pytest.raises(ValueError, match=error_msg):
                read_transform(
                    storage=matrix_storage_with_nan,  # type: ignore
                    feature_name="BOLD_matrix",
                    transform="bctpy_eigenvector_centrality_und",
                    nan_policy=nan_policy,
                )
