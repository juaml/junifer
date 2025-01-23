"""Provide tests for HDF5 storage interface."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
#          Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from copy import deepcopy
from pathlib import Path

import h5py
import numpy as np
import pytest
from numpy.testing import assert_array_equal
from pandas.testing import assert_frame_equal

from junifer.storage import HDF5FeatureStorage
from junifer.storage.utils import (
    element_to_prefix,
    matrix_to_vector,
    process_meta,
)


def test_get_valid_inputs() -> None:
    """Test valid inputs."""
    storage = HDF5FeatureStorage(uri="/tmp")
    assert storage.get_valid_inputs() == [
        "matrix",
        "vector",
        "timeseries",
        "scalar_table",
    ]


def test_single_output(tmp_path: Path) -> None:
    """Test single output setup.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_single_output.hdf5"
    # Single storage, must be the uri
    storage = HDF5FeatureStorage(uri=uri, single_output=True)
    assert storage.single_output is True


def test_multi_output_error(tmp_path: Path) -> None:
    """Test error for multi output.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_multi_output.hdf5"
    storage = HDF5FeatureStorage(uri=uri, single_output=False)
    with pytest.raises(RuntimeError, match="`element` must be provided"):
        storage._fetch_correct_uri_for_io(element=None)


def test_single_output_parent_path_creation(tmp_path: Path) -> None:
    """Test path creation with single output creation.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    to_create_hdf5 = tmp_path / "to_create_hdf5"
    # Path does not exist yet
    assert not to_create_hdf5.exists()

    uri = to_create_hdf5.absolute() / "test_single_output.hdf5"
    _ = HDF5FeatureStorage(uri=uri, single_output=True)
    # Path exists now
    assert to_create_hdf5.exists()


def test_read_metadata_file_not_found_error(tmp_path: Path) -> None:
    """Test file not found error when reading metadata.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_read_metadata_no_file.hdf5"
    storage = HDF5FeatureStorage(uri=uri, single_output=True)
    # Check file not found error
    with pytest.raises(FileNotFoundError, match="HDF5 file not found at:"):
        storage._read_metadata()


def test_read_metadata_meta_not_found_error(tmp_path: Path) -> None:
    """Test meta not found error when reading metadata.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_read_metadata_no_meta.hdf5"
    storage = HDF5FeatureStorage(uri=uri, single_output=True)
    # Create file
    with h5py.File(uri, "w") as f:
        f.create_dataset("mydataset", (100,), dtype="i")
    # Check meta not found error
    with pytest.raises(RuntimeError, match="Invalid junifer HDF5 file at:"):
        storage._read_metadata()


def test_read_data_file_not_found_error(tmp_path: Path) -> None:
    """Test file not found error when reading data.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_read_data_no_file.hdf5"
    storage = HDF5FeatureStorage(uri=uri, single_output=True)
    # Check file not found error
    with pytest.raises(FileNotFoundError, match="HDF5 file not found at:"):
        storage._read_data(md5="md5")


def test_read_data_md5_not_found_error(tmp_path: Path) -> None:
    """Test meta not found error when reading data.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_read_data_no_md5.hdf5"
    storage = HDF5FeatureStorage(uri=uri, single_output=True)
    # Create file
    with h5py.File(uri, "w") as f:
        f.create_dataset("mydataset", (100,), dtype="i")
    # Check MD5 not found error
    with pytest.raises(RuntimeError, match="not found in HDF5 file at:"):
        storage._read_data(md5="md5")


def test_store_metadata_and_list_features(tmp_path: Path) -> None:
    """Test metadata store and features listing.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_metadata_store.hdf5"
    # Single storage, must be the uri
    storage = HDF5FeatureStorage(uri=uri, single_output=True)
    # Metadata to store
    meta = {
        "element": {"subject": "test"},
        "dependencies": ["numpy"],
        "marker": {"name": "test"},
        "type": "BOLD",
    }
    # Process the metadata
    meta_md5, meta_to_store, element_to_store = process_meta(meta)
    # Store metadata
    storage.store_metadata(
        meta_md5=meta_md5, element=element_to_store, meta=meta_to_store
    )
    # List the stored features
    features = storage.list_features()
    # Get the first MD5
    feature_md5 = next(iter(features.keys()))
    # Check the MD5
    assert meta_md5 == feature_md5


def test_store_metadata_ignore_duplicate(tmp_path: Path) -> None:
    """Test duplicate ignore for metadata store.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_duplicate_metadata_store.hdf5"
    # Single storage, must be the uri
    storage = HDF5FeatureStorage(uri=uri, single_output=True)
    # Store metadata first time
    storage.store_metadata(
        meta_md5="md5",
        element={"sub": "001"},
        meta={
            "element": {"subject": "test"},
            "dependencies": ["numpy"],
            "marker": {"name": "test"},
            "type": "BOLD",
        },
    )
    # Store metadata second time, should be ignored
    storage.store_metadata(
        meta_md5="md5",
        element={"sub": "001"},
        meta={
            "element": {"subject": "test"},
            "dependencies": ["numpy"],
            "marker": {"name": "test"},
            "type": "BOLD",
        },
    )
    # List the stored features
    features = storage.list_features()
    # Should only have one element
    assert len(features) == 1


def test_read(tmp_path: Path) -> None:
    """Test read.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_read.hdf5"
    storage = HDF5FeatureStorage(uri=uri)
    # Data to store
    to_store_data = {
        "meta": {
            "element": {"subject": "test"},
            "dependencies": ["numpy"],
            "marker": {"name": "test"},
            "type": "BOLD",
        },
        "data": np.array([[1, 10]]),
        "col_names": ["f1", "f2"],
    }
    # Store data
    storage.store(kind="vector", **to_store_data)
    # Read and check
    stored_data = storage.read(feature_name="BOLD_test")
    assert ["column_headers", "data", "element", "kind"] == list(
        stored_data.keys()
    )


def test_read_df_params_error(tmp_path: Path) -> None:
    """Test parameter validation errors for read_df.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_read_df_params_error.hdf5"
    storage = HDF5FeatureStorage(uri=uri, single_output=True)
    # Store metadata to create the file
    storage.store_metadata(
        meta_md5="meta_md5",
        element={"sub": "001"},
        meta={
            "element": {"subject": "test"},
            "dependencies": ["numpy"],
            "marker": {"name": "test"},
            "name": "BOLD",
        },
    )

    with pytest.raises(ValueError, match="Only one of"):
        storage.read_df(feature_name="name", feature_md5="md5")

    with pytest.raises(ValueError, match="At least one of"):
        storage.read_df()

    with pytest.raises(ValueError, match="Feature MD5"):
        storage.read_df(feature_md5="md5")


def test_read_df(tmp_path: Path) -> None:
    """Test read_df.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_read_df.hdf5"
    storage = HDF5FeatureStorage(uri=uri)
    # Metadata to store
    meta = {
        "element": {"subject": "test"},
        "dependencies": ["numpy"],
        "marker": {"name": "test"},
        "type": "BOLD",
    }
    # Process the metadata
    meta_md5, meta_to_store, element_to_store = process_meta(meta)
    # Store metadata
    storage.store_metadata(
        meta_md5=meta_md5, element=element_to_store, meta=meta_to_store
    )
    # Data to store
    data = np.array([[1, 10]])
    col_headers = ["f1", "f2"]
    # Store table
    storage.store_vector(
        meta_md5=meta_md5,
        element=element_to_store,
        data=data,
        col_names=col_headers,
    )
    # Read into dataframe and check
    df_md5 = storage.read_df(feature_md5=meta_md5)
    df_name = storage.read_df(feature_name="BOLD_test")
    assert_frame_equal(df_md5, df_name)

    # Check for errors about no / duplicate feature name
    with pytest.raises(ValueError, match="not found"):
        storage.read_df(feature_name="BOLD")

    # Store duplicate entry and check error
    storage.store_metadata(
        meta_md5=meta_md5,
        element={"subject": "test-clone"},
        meta=meta_to_store,
    )
    storage.store_vector(
        meta_md5=meta_md5,
        element={"subject": "test-clone"},
        data=data,
        col_names=col_headers,
    )


@pytest.mark.parametrize(
    "force, dtype",
    [
        (True, "float32"),
        (False, "float64"),
    ],
)
def test_f64_to_f632_conversion(
    tmp_path: Path, force: bool, dtype: str
) -> None:
    """Test actual data is casted from float64 to float32.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    force : bool
        The parametrized conversion option.
    dtype : str
        The parametrized expected data type.

    """
    uri = tmp_path / "test_data_conversion.hdf5"
    storage = HDF5FeatureStorage(uri=uri, force_float32=force)
    # Metadata to store
    meta = {
        "element": {"subject": "test"},
        "dependencies": ["numpy"],
        "marker": {"name": "mark"},
        "type": "BOLD",
    }
    # Process the metadata
    meta_md5, meta_to_store, element_to_store = process_meta(meta)
    # Store matrix
    storage.store_metadata(
        meta_md5=meta_md5, element=element_to_store, meta=meta_to_store
    )
    # Store data
    storage.store_matrix(
        meta_md5=meta_md5,
        element=element_to_store,
        data=np.arange(4, dtype="float64").reshape((2, 2)),
    )
    # Read into dataframe
    read_df = storage.read_df(feature_md5=meta_md5)
    # Check data type
    assert read_df.values.dtype == np.dtype(dtype)


def test_store_matrix(tmp_path: Path) -> None:
    """Test matrix store.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_store_matrix.hdf5"
    storage = HDF5FeatureStorage(uri=uri)
    # Metadata to store
    meta = {
        "element": {"subject": "test"},
        "dependencies": ["numpy"],
        "marker": {"name": "fc"},
        "type": "BOLD",
    }
    # Process the metadata
    meta_md5, meta_to_store, element_to_store = process_meta(meta)
    # Store metadata
    storage.store_metadata(
        meta_md5=meta_md5, element=element_to_store, meta=meta_to_store
    )

    # Store 4 X 3 full matrix
    data = np.array(
        [[1, 2, 3], [11, 22, 33], [111, 222, 333], [1111, 2222, 3333]]
    )
    row_headers = ["row1", "row2", "row3", "row4"]
    col_headers = ["col1", "col2", "col3"]

    # Store matrix
    storage.store_matrix(
        meta_md5=meta_md5,
        element=element_to_store,
        data=data,
        row_names=row_headers,
        col_names=col_headers,
    )

    # List the stored features
    features = storage.list_features()
    # Check the MD5
    assert "BOLD_fc" == features[meta_md5]["name"]

    # Read into dataframe
    read_df = storage.read_df(feature_md5=meta_md5)
    # Check shape of dataframe
    assert read_df.shape == (1, 12)
    # Check data of dataframe
    assert_array_equal(read_df.values, data.reshape(1, -1))
    # Check column headers
    assert read_df.columns.to_list() == [
        f"{row}~{col}" for row in row_headers for col in col_headers
    ]


def test_store_matrix_without_headers(tmp_path: Path) -> None:
    """Test matrix store without headers.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_store_matrix_no_headers.hdf5"
    storage = HDF5FeatureStorage(uri=uri)
    # Metadata to store
    meta = {
        "element": {"subject": "test"},
        "dependencies": ["numpy"],
        "marker": {"name": "fc"},
        "type": "BOLD",
    }
    # Process the metadata
    meta_md5, meta_to_store, element_to_store = process_meta(meta)
    # Store metadata
    storage.store_metadata(
        meta_md5=meta_md5, element=element_to_store, meta=meta_to_store
    )

    # Store 4 X 3 full matrix
    data = np.array(
        [[1, 2, 3], [11, 22, 33], [111, 222, 333], [1111, 2222, 3333]]
    )

    # Store matrix
    storage.store_matrix(
        meta_md5=meta_md5, element=element_to_store, data=data
    )

    # List the stored features
    features = storage.list_features()
    # Check the MD5
    assert "BOLD_fc" == features[meta_md5]["name"]

    # Read the dataframe
    read_df = storage.read_df(feature_md5=meta_md5)
    # Check shape of dataframe
    assert read_df.shape == (1, 12)
    # Check data of dataframe
    assert_array_equal(read_df.values, data.reshape(1, -1))
    # Check column headers
    assert read_df.columns.to_list() == [
        f"{row}~{col}"
        for row in ["r0", "r1", "r2", "r3"]
        for col in ["c0", "c1", "c2"]
    ]


def test_store_upper_triangular_matrix(tmp_path: Path) -> None:
    """Test upper triangular matrix store.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_store_matrix_triu.hdf5"
    storage = HDF5FeatureStorage(uri=uri)
    # Metadata to store
    meta = {
        "element": {"subject": "test"},
        "dependencies": ["numpy"],
        "marker": {"name": "fc"},
        "type": "BOLD",
    }
    # Process the metadata
    meta_md5, meta_to_store, element_to_store = process_meta(meta)
    # Store metadata
    storage.store_metadata(
        meta_md5=meta_md5, element=element_to_store, meta=meta_to_store
    )

    # Store upper triangular matrix
    data = np.array([[1, 2, 3], [11, 22, 33], [111, 222, 333]])
    row_headers = ["row1", "row2", "row3"]
    col_headers = ["col1", "col2", "col3"]

    # Store matrix
    storage.store_matrix(
        meta_md5=meta_md5,
        element=element_to_store,
        data=data,
        row_names=row_headers,
        col_names=col_headers,
        matrix_kind="triu",
    )

    # List the stored features
    features = storage.list_features()
    # Check the MD5
    assert "BOLD_fc" == features[meta_md5]["name"]

    # Read into dataframe
    read_df = storage.read_df(feature_md5=meta_md5)
    # Check data of dataframe
    assert_array_equal(read_df.values, np.array([[1, 2, 3, 22, 33, 333]]))
    # Check column headers
    assert read_df.columns.to_list() == [
        "row1~col1",
        "row1~col2",
        "row1~col3",
        "row2~col2",
        "row2~col3",
        "row3~col3",
    ]


def test_store_upper_triangular_matrix_without_diagonal(
    tmp_path: Path,
) -> None:
    """Test upper triangular matrix without diagonal store.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_store_matrix_triu_no_diagonal.hdf5"
    storage = HDF5FeatureStorage(uri=uri)
    # Metadata to store
    meta = {
        "element": {"subject": "test"},
        "dependencies": ["numpy"],
        "marker": {"name": "fc"},
        "type": "BOLD",
    }
    # Process the metadata
    meta_md5, meta_to_store, element_to_store = process_meta(meta)
    # Store metadata
    storage.store_metadata(
        meta_md5=meta_md5, element=element_to_store, meta=meta_to_store
    )

    # Store upper triangular matrix without diagonal
    data = np.array([[1, 2, 3], [11, 22, 33], [111, 222, 333]])
    row_headers = ["row1", "row2", "row3"]
    col_headers = ["col1", "col2", "col3"]

    # Store matrix
    storage.store_matrix(
        meta_md5=meta_md5,
        element=element_to_store,
        data=data,
        row_names=row_headers,
        col_names=col_headers,
        matrix_kind="triu",
        diagonal=False,
    )

    # List the stored features
    features = storage.list_features()
    # Check the MD5
    assert "BOLD_fc" == features[meta_md5]["name"]

    # Read into dataframe
    read_df = storage.read_df(feature_md5=meta_md5)
    # Check data of dataframe
    assert_array_equal(read_df.values, np.array([[2, 3, 33]]))
    # Check column headers
    assert read_df.columns.to_list() == ["row1~col2", "row1~col3", "row2~col3"]


def test_store_lower_triangular_matrix(tmp_path: Path) -> None:
    """Test lower triangular matrix store.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_store_matrix_tril.hdf5"
    storage = HDF5FeatureStorage(uri=uri)
    # Metadata to store
    meta = {
        "element": {"subject": "test"},
        "dependencies": ["numpy"],
        "marker": {"name": "fc"},
        "type": "BOLD",
    }
    # Process the metadata
    meta_md5, meta_to_store, element_to_store = process_meta(meta)
    # Store metadata
    storage.store_metadata(
        meta_md5=meta_md5, element=element_to_store, meta=meta_to_store
    )

    # Store lower triangular matrix
    data = np.array([[1, 2, 3], [11, 22, 33], [111, 222, 333]])
    row_headers = ["row1", "row2", "row3"]
    col_headers = ["col1", "col2", "col3"]

    # Store matrix
    storage.store_matrix(
        meta_md5=meta_md5,
        element=element_to_store,
        data=data,
        row_names=row_headers,
        col_names=col_headers,
        matrix_kind="tril",
    )

    # List the stored features
    features = storage.list_features()
    # Check the MD5
    assert "BOLD_fc" == features[meta_md5]["name"]

    # Read into dataframe
    read_df = storage.read_df(feature_md5=meta_md5)
    # Check data of dataframe
    assert_array_equal(read_df.values, np.array([[1, 11, 22, 111, 222, 333]]))
    # Check column headers
    assert read_df.columns.to_list() == [
        "row1~col1",
        "row2~col1",
        "row2~col2",
        "row3~col1",
        "row3~col2",
        "row3~col3",
    ]


def test_store_lower_triangular_matrix_without_diagonal(
    tmp_path: Path,
) -> None:
    """Test lower triangular matrix without diagonal store.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_store_matrix_tril_no_diagonal.hdf5"
    storage = HDF5FeatureStorage(uri=uri)
    # Metadata to store
    meta = {
        "element": {"subject": "test"},
        "dependencies": ["numpy"],
        "marker": {"name": "fc"},
        "type": "BOLD",
    }
    # Process the metadata
    meta_md5, meta_to_store, element_to_store = process_meta(meta)
    # Store metadata
    storage.store_metadata(
        meta_md5=meta_md5, element=element_to_store, meta=meta_to_store
    )

    # Store lower triangular matrix without diagonal
    data = np.array([[1, 2, 3], [11, 22, 33], [111, 222, 333]])
    row_headers = ["row1", "row2", "row3"]
    col_headers = ["col1", "col2", "col3"]

    # Store matrix
    storage.store_matrix(
        meta_md5=meta_md5,
        element=element_to_store,
        data=data,
        row_names=row_headers,
        col_names=col_headers,
        matrix_kind="tril",
        diagonal=False,
    )

    # List the stored features
    features = storage.list_features()
    # Check the MD5
    assert "BOLD_fc" == features[meta_md5]["name"]

    # Read into dataframe
    read_df = storage.read_df(feature_md5=meta_md5)
    # Check data of dataframe
    assert_array_equal(read_df.values, np.array([[11, 111, 222]]))
    # Check column headers
    assert read_df.columns.to_list() == ["row2~col1", "row3~col1", "row3~col2"]


def test_store_vector(tmp_path: Path) -> None:
    """Test vector store.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_store_vector.hdf5"
    storage = HDF5FeatureStorage(uri=uri)
    # Metadata to store
    element = {"subject": "test"}
    meta = {
        "element": element,
        "dependencies": ["numpy"],
        "marker": {"name": "fc"},
        "type": "BOLD",
    }
    # Process the metadata
    meta_md5, meta_to_store, element_to_store = process_meta(meta)
    # Store metadata
    storage.store_metadata(
        meta_md5=meta_md5, element=element_to_store, meta=meta_to_store
    )

    # Data to store
    data = [10, 20, 30, 40, 50]
    col_names = ["f1", "f2", "f3", "f4", "f5"]

    # Store vector
    storage.store_vector(
        meta_md5=meta_md5,
        element=element_to_store,
        data=data,
        col_names=col_names,
    )

    # Read into dataframe
    read_df = storage.read_df(feature_md5=meta_md5)
    # Check if data are equal
    assert read_df.values.flatten().tolist() == data


def test_store_timeseries(tmp_path: Path) -> None:
    """Test timeseries store.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_store_timeseries.hdf5"
    storage = HDF5FeatureStorage(uri=uri)
    # Metadata to store
    element = {"subject": "test"}
    meta = {
        "element": element,
        "dependencies": ["numpy"],
        "marker": {"name": "fc"},
        "type": "BOLD",
    }
    # Process the metadata
    meta_md5, meta_to_store, element_to_store = process_meta(meta)
    # Store metadata
    storage.store_metadata(
        meta_md5=meta_md5, element=element_to_store, meta=meta_to_store
    )

    # Data to store
    data = np.array([[10], [20], [30], [40], [50]])
    col_names = ["signal"]

    # Store timeseries
    storage.store_timeseries(
        meta_md5=meta_md5,
        element=element_to_store,
        data=data,
        col_names=col_names,
    )

    # Read into dataframe
    read_df = storage.read_df(feature_md5=meta_md5)
    # Check if data are equal
    assert_array_equal(read_df.values, data)


def test_store_timeseries2d(tmp_path: Path) -> None:
    """Test 2D timeseries store.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_store_timeseries_2d.hdf5"
    storage = HDF5FeatureStorage(uri=uri)
    # Metadata to store
    element = {"subject": "test"}
    meta = {
        "element": element,
        "dependencies": ["numpy"],
        "marker": {"name": "fc"},
        "type": "BOLD",
    }
    # Process the metadata
    meta_md5, meta_to_store, element_to_store = process_meta(meta)
    # Store metadata
    storage.store_metadata(
        meta_md5=meta_md5, element=element_to_store, meta=meta_to_store
    )

    # Data to store
    data = np.array(
        [[10, 11, 12], [20, 21, 22], [30, 31, 32], [40, 41, 42], [50, 51, 52]]
    )
    data = np.c_[[data + (i * 100) for i in range(4)]]  # Generate timeseries

    col_names = ["roi1", "roi2", "roi3"]
    row_names = ["ev1", "ev2", "ev3", "ev4", "ev5"]

    # Store 2D timeseries
    storage.store_timeseries_2d(
        meta_md5=meta_md5,
        element=element_to_store,
        data=data,
        col_names=col_names,
        row_names=row_names,
    )

    # Read into dataframe
    read_data = storage.read(feature_md5=meta_md5)
    # Check if data are equal
    assert_array_equal(read_data["data"][0], data)
    assert read_data["column_headers"] == col_names
    assert read_data["row_headers"], row_names

    read_df = storage.read_df(feature_md5=meta_md5)
    flatted_names = [f"{row}~{col}" for row in row_names for col in col_names]

    expected_flat_data = np.array(
        [10, 11, 12, 20, 21, 22, 30, 31, 32, 40, 41, 42, 50, 51, 52]
    )
    expected_flat_data = np.c_[
        [expected_flat_data + (i * 100) for i in range(4)]
    ]  # Generate timeseries
    assert_array_equal(read_df.values, expected_flat_data)
    assert read_df.columns.to_list() == flatted_names


def test_store_scalar_table(tmp_path: Path) -> None:
    """Test scalar table store.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_store_scalar_table.hdf5"
    storage = HDF5FeatureStorage(uri=uri)
    # Metadata to store
    element = {"subject": "test"}
    meta = {
        "element": element,
        "dependencies": ["numpy"],
        "marker": {"name": "brainprint"},
        "type": "FreeSurfer",
    }
    # Process the metadata
    meta_md5, meta_to_store, element_to_store = process_meta(meta)
    # Store metadata
    storage.store_metadata(
        meta_md5=meta_md5, element=element_to_store, meta=meta_to_store
    )

    # Data to store
    data = np.array([[10, 20], [30, 40], [50, 60]])
    col_names = ["roi1", "roi2"]
    row_names = ["ev1", "ev2", "ev3"]

    # Store scalar table
    storage.store_scalar_table(
        meta_md5=meta_md5,
        element=element_to_store,
        data=data,
        col_names=col_names,
        row_names=row_names,
        row_header_col_name="eigenvalue",
    )

    # Read into dataframe
    read_df = storage.read_df(feature_md5=meta_md5)
    # Check if data are equal
    assert_array_equal(read_df.values, data)


def _create_data_to_store(n_elements: int, kind: str) -> tuple[str, dict]:
    """Create data to store.

    Parameters
    ----------
    n_elements : int
        The number of elements to create.
    kind : str
        The kind of data to create.

    Returns
    -------
    str
        The meta md5.
    dict
        The data to store.

    """
    all_data = []
    t_md5 = None
    if kind == "vector":
        data_to_store = {
            "data": np.arange(10),
            "col_names": [f"col-{i}" for i in range(10)],
        }
    elif kind == "matrix":
        data_to_store = {
            "data": np.arange(100).reshape(10, 10),
            "row_names": [f"row-{i}" for i in range(10)],
            "col_names": [f"col-{i}" for i in range(10)],
            "matrix_kind": "full",
        }
    elif kind in "timeseries":
        data_to_store = {
            "data": np.arange(20).reshape(2, 10),
            "col_names": [f"col-{i}" for i in range(10)],
        }
    elif kind in "timeseries_2d":
        data_to_store = {
            "data": np.arange(120).reshape(6, 5, 4),
            "row_names": [f"row-{i}" for i in range(5)],
            "col_names": [f"col-{i}" for i in range(4)],
        }
    elif kind in "scalar_table":
        data_to_store = {
            "data": np.arange(50).reshape(5, 10),
            "row_names": [f"row-{i}" for i in range(5)],
            "col_names": [f"col-{i}" for i in range(10)],
            "row_header_col_name": "row",
        }

    for i in range(n_elements):
        element = {"subject": f"sub-{i // 2}", "session": f"ses-{i % 2}"}
        meta = {
            "element": element,
            "dependencies": ["numpy"],
            "marker": {"name": f"test-{kind}"},
            "type": "BOLD",
        }
        # Process the metadata
        meta_md5, meta_to_store, element_to_store = process_meta(meta)
        if kind == "timeseries":
            t_data = data_to_store["data"]
            data_to_store["data"] = np.r_[
                t_data, (t_data[-1, :] + t_data[-1, :])[None]
            ]
        else:
            data_to_store["data"] = data_to_store["data"] + i

        if t_md5 is None:
            t_md5 = meta_md5
        else:
            assert t_md5 == meta_md5

        # Store metadata
        all_data.append(
            {
                "element": element_to_store,
                "meta": meta_to_store,
                "data": deepcopy(data_to_store),
            }
        )
    return t_md5, all_data


@pytest.mark.parametrize(
    "n_elements, chunk_size, kind",
    [
        (10, 3, "vector"),
        (10, 5, "vector"),
        (10, 3, "matrix"),
        (10, 5, "matrix"),
        (10, 5, "timeseries"),
        (10, 5, "scalar_table"),
        (10, 5, "timeseries_2d"),
    ],
)
def test_multi_output_store_and_collect(
    tmp_path: Path, n_elements: int, chunk_size: int, kind: str
) -> None:
    """Test multi output storing and collection.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    n_elements : int
        The parametrized element count.
    chunk_size : int
        The parametrized chunk size.
    kind : str
        The parametrized storage kind.

    """
    uri = tmp_path / "test_multi_output_store_and_collect.hdf5"
    storage = HDF5FeatureStorage(
        uri=uri,
        single_output=False,
        chunk_size=chunk_size,
    )

    meta_md5, all_data = _create_data_to_store(n_elements, kind)

    for t_data in all_data:
        # Store metadata
        storage.store_metadata(
            meta_md5=meta_md5,
            element=t_data["element"],
            meta=t_data["meta"],
        )
        # Store data
        if kind == "vector":
            storage.store_vector(
                meta_md5=meta_md5,
                element=t_data["element"],
                **t_data["data"],
            )
        elif kind == "matrix":
            storage.store_matrix(
                meta_md5=meta_md5,
                element=t_data["element"],
                **t_data["data"],
            )
        elif kind == "timeseries":
            storage.store_timeseries(
                meta_md5=meta_md5,
                element=t_data["element"],
                **t_data["data"],
            )
        elif kind == "timeseries_2d":
            storage.store_timeseries_2d(
                meta_md5=meta_md5,
                element=t_data["element"],
                **t_data["data"],
            )
        elif kind == "scalar_table":
            storage.store_scalar_table(
                meta_md5=meta_md5,
                element=t_data["element"],
                **t_data["data"],
            )
    # Check that base URI does not exist yet
    assert not uri.exists()

    for t_data in all_data:
        # Convert element to prefix
        prefix = element_to_prefix(t_data["element"])
        # URIs for data storage
        elem_uri = uri.parent / f"{prefix}{uri.name}"
        # Check URIs for data storage exist
        assert elem_uri.exists()

        # Read stored metadata from different files using element
        read_meta = storage._read_metadata(element=t_data["element"])
        # Check if metadata are equal
        assert read_meta == {meta_md5: t_data["meta"]}

    # Collect data
    storage.collect()
    # Check that base URI exists now
    assert uri.exists()

    # Read unified metadata
    read_unified_meta = storage.list_features()
    assert meta_md5 in read_unified_meta

    # Check if aggregated metadata are equal
    assert all(x["meta"] == read_unified_meta[meta_md5] for x in all_data)

    all_df = storage.read_df(feature_md5=meta_md5)
    if kind == "timeseries":
        data_size = np.sum([x["data"]["data"].shape[0] for x in all_data])
        assert len(all_df) == data_size
        idx_names = [x for x in all_df.index.names if x != "timepoint"]
    elif kind == "timeseries_2d":
        data_size = np.sum([x["data"]["data"].shape[0] for x in all_data])
        assert len(all_df) == data_size
        idx_names = [x for x in all_df.index.names if x != "timepoint"]
    elif kind == "scalar_table":
        data_size = np.sum([x["data"]["data"].shape[0] for x in all_data])
        assert len(all_df) == data_size
        idx_names = [x for x in all_df.index.names if x != "row"]
    else:
        assert len(all_df) == len(all_data)
        idx_names = all_df.index.names
    for t_data in all_data:
        t_series = all_df.loc[tuple([t_data["element"][v] for v in idx_names])]
        if kind == "vector":
            assert_array_equal(t_series.values, t_data["data"]["data"])
            series_names = t_series.index.values.tolist()
            assert series_names == t_data["data"]["col_names"]
        elif kind == "matrix":
            flat_data, columns = matrix_to_vector(
                t_data["data"]["data"],
                col_names=t_data["data"]["col_names"],
                row_names=t_data["data"]["row_names"],
                matrix_kind="full",
                diagonal=True,
            )
            assert_array_equal(t_series.values, flat_data)
            series_names = t_series.index.values.tolist()
            assert series_names == columns
        elif kind == "timeseries":
            assert_array_equal(t_series.values, t_data["data"]["data"])
            series_names = t_series.columns.values.tolist()
            assert series_names == t_data["data"]["col_names"]
        elif kind == "scalar_table":
            assert_array_equal(t_series.values, t_data["data"]["data"])
            series_names = t_series.columns.values.tolist()
            assert series_names == t_data["data"]["col_names"]


def test_collect_error_single_output() -> None:
    """Test error for collect in single output storage."""
    with pytest.raises(
        NotImplementedError,
        match="is not implemented for single output.",
    ):
        storage = HDF5FeatureStorage(uri="/tmp", single_output=True)
        storage.collect()
