"""Provide tests for HDF5 storage interface."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
#          Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_array_equal
from pandas.testing import assert_frame_equal

from junifer.storage import HDF5FeatureStorage
from junifer.storage.utils import element_to_prefix, process_meta


def test_get_valid_inputs() -> None:
    """Test valid inputs."""
    storage = HDF5FeatureStorage(uri="/tmp")
    assert storage.get_valid_inputs() == ["matrix", "table", "timeseries"]


def test_single_output(tmp_path: Path) -> None:
    """Test engine retrieval with single output.

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
    feature_md5 = list(features.keys())[0]
    # Check the MD5
    assert meta_md5 == feature_md5


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
    # Get the first MD5
    feature_md5 = list(features.keys())[0]
    # Check the MD5
    assert "BOLD_fc" == features[feature_md5]["name"]

    # Read into dataframe
    read_df = storage.read_df(feature_md5=feature_md5)
    # Check shape of dataframe
    assert read_df.shape == (1, 12)
    # Check data of dataframe
    assert_array_equal(read_df.values[0], data.flatten())

    # Format column headers
    stored_col_headers = [f"{i}~{j}" for i in row_headers for j in col_headers]
    # Check column headers
    assert list(read_df.columns) == stored_col_headers

    # Check for errors
    with pytest.raises(ValueError, match="Invalid kind"):
        storage.store_matrix(
            meta_md5=meta_md5,
            element=element_to_store,
            data=data,
            row_names=row_headers,
            col_names=col_headers,
            matrix_kind="wrong",
        )

    with pytest.raises(ValueError, match="non-square"):
        storage.store_matrix(
            meta_md5=meta_md5,
            element=element_to_store,
            data=data,
            row_names=row_headers,
            col_names=col_headers,
            matrix_kind="triu",
        )

    with pytest.raises(ValueError, match="cannot be False"):
        storage.store_matrix(
            meta_md5=meta_md5,
            element=element_to_store,
            data=data,
            row_names=row_headers,
            col_names=col_headers,
            matrix_kind="full",
            diagonal=False,
        )


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
    # Get the first MD5
    feature_md5 = list(features.keys())[0]
    # Check the MD5
    assert "BOLD_fc" == features[feature_md5]["name"]

    # Read the dataframe
    read_df = storage.read_df(feature_md5=feature_md5)
    # Check shape of dataframe
    assert read_df.shape == (1, 12)
    # Check data of dataframe
    assert_array_equal(read_df.values[0], data.flatten())

    # Format column headers
    stored_col_headers = [
        f"r{i}~c{j}"
        for i in range(data.shape[0])
        for j in range(data.shape[1])
    ]
    # Check column headers
    assert list(read_df.columns) == stored_col_headers


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
    # Get the first MD5
    feature_md5 = list(features.keys())[0]
    # Check the MD5
    assert "BOLD_fc" == features[feature_md5]["name"]

    # Read into dataframe
    read_df = storage.read_df(feature_md5=feature_md5)
    # Check data of dataframe
    assert_array_equal(
        read_df.values, data[np.triu_indices(n=data.shape[0])][None, :]
    )

    # Format column headers
    stored_col_headers = [
        "row1~col1",
        "row1~col2",
        "row1~col3",
        "row2~col2",
        "row2~col3",
        "row3~col3",
    ]
    # Check column headers
    assert list(read_df.columns) == stored_col_headers


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
    # Get the first MD5
    feature_md5 = list(features.keys())[0]
    # Check the MD5
    assert "BOLD_fc" == features[feature_md5]["name"]

    # Read into dataframe
    read_df = storage.read_df(feature_md5=feature_md5)
    # Check data of dataframe
    assert_array_equal(
        read_df.values, data[np.triu_indices(n=data.shape[0], k=1)][None, :]
    )

    # Format column headers
    stored_col_headers = [
        "row1~col2",
        "row1~col3",
        "row2~col3",
    ]
    # Check column headers
    assert list(read_df.columns) == stored_col_headers


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
    # Get the first MD5
    feature_md5 = list(features.keys())[0]
    # Check the MD5
    assert "BOLD_fc" == features[feature_md5]["name"]

    # Read into dataframe
    read_df = storage.read_df(feature_md5=feature_md5)
    # Check data of dataframe
    assert_array_equal(
        read_df.values, data[np.tril_indices(n=data.shape[0])][None, :]
    )

    # Format column headers
    stored_col_headers = [
        "row1~col1",
        "row2~col1",
        "row2~col2",
        "row3~col1",
        "row3~col2",
        "row3~col3",
    ]
    # Check column headers
    assert list(read_df.columns) == stored_col_headers


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
    # Get the first MD5
    feature_md5 = list(features.keys())[0]
    # Check the MD5
    assert "BOLD_fc" == features[feature_md5]["name"]

    # Read into dataframe
    read_df = storage.read_df(feature_md5=feature_md5)
    # Check data of dataframe
    assert_array_equal(
        read_df.values, data[np.tril_indices(n=data.shape[0], k=-1)][None, :]
    )

    # Format column headers
    stored_col_headers = [
        "row2~col1",
        "row3~col1",
        "row3~col2",
    ]
    # Check column headers
    assert list(read_df.columns) == stored_col_headers


def test_store_table(tmp_path: Path) -> None:
    """Test table store.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_store_table.hdf5"
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
        [
            [1, 10],
            [2, 20],
            [3, 30],
            [4, 40],
            [5, 50],
        ]
    )
    row_header = "scan"
    col_headers = ["f1", "f2"]

    # Store table
    storage.store_table(
        meta_md5=meta_md5,
        element=element_to_store,
        data=data,
        columns=col_headers,
        rows_col_name=row_header,
    )

    # Convert element to index dict
    idx_dict = storage._element_metadata_to_index_dict(
        element=element,
        n_rows=5,
        row_headers="scan",
    )
    # Convert index dict to index
    idx = storage._index_dict_to_multiindex(
        index_dict=idx_dict["idx_data"],  # type: ignore
        index_columns_order=idx_dict["idx_columns_order"],  # type: ignore
        n_rows=idx_dict["n_rows"],  # type: ignore
    )
    # Create dataframe
    df = pd.DataFrame(data, columns=["f1", "f2"], index=idx)

    # Read into dataframe
    read_df = storage.read_df(feature_md5=meta_md5)
    # Check if dataframes are equal
    assert_frame_equal(df, read_df)

    # New data to store
    data_new = np.array(
        [[1, 10], [2, 20], [3, 300], [4, 40], [5, 50], [6, 600]]
    )
    # Convert element to index dict
    idx_dict_new = storage._element_metadata_to_index_dict(
        element=element,
        n_rows=6,
        row_headers="scan",
    )
    # Convert index dict to index
    idx_new = storage._index_dict_to_multiindex(
        index_dict=idx_dict_new["idx_data"],  # type: ignore
        index_columns_order=idx_dict_new["idx_columns_order"],  # type: ignore
        n_rows=idx_dict_new["n_rows"],  # type: ignore
    )
    # Create new dataframe
    df_new = pd.DataFrame(data_new, columns=["f1", "f2"], index=idx_new)

    # Store table
    storage.store_table(
        meta_md5=meta_md5,
        element=element_to_store,
        data=data_new,
        columns=["f1", "f2"],
        rows_col_name="scan",
    )

    # Read into dataframe
    read_df_new = storage.read_df(feature_md5=meta_md5)
    # Check if dataframes are equal
    assert_frame_equal(df_new, read_df_new)


def test_multi_output_store_and_collect(tmp_path: Path):
    """Test multi output storing and collection.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_multi_output_store_and_collect.hdf5"
    storage = HDF5FeatureStorage(uri=uri, single_output=False)

    # Metadata to store
    meta_1 = {
        "element": {"subject": "test-01", "session": "ses-01"},
        "dependencies": ["numpy"],
        "marker": {"name": "fc"},
        "type": "BOLD",
    }
    meta_2 = {
        "element": {"subject": "test-02", "session": "ses-01"},
        "dependencies": ["numpy"],
        "marker": {"name": "fc"},
        "type": "BOLD",
    }
    meta_3 = {
        "element": {"subject": "test-01", "session": "ses-02"},
        "dependencies": ["numpy"],
        "marker": {"name": "fc"},
        "type": "BOLD",
    }

    # Data to store
    data_1 = np.array(
        [
            [1, 10],
            [2, 20],
            [3, 30],
            [4, 40],
            [5, 50],
        ]
    )
    data_2 = data_1 * 10
    data_3 = data_1 * 20
    row_header = "scan"
    col_headers = ["f1", "f2"]

    # Process metadata for storage
    hash_1, meta_to_store_1, element_to_store_1 = process_meta(meta_1)

    # Process metadata for storage
    hash_2, meta_to_store_2, element_to_store_2 = process_meta(meta_2)

    # Process metadata for storage
    hash_3, meta_to_store_3, element_to_store_3 = process_meta(meta_3)

    # Check hash equality as element is not considered for hash
    assert hash_1 == hash_2
    assert hash_2 == hash_3

    # Store metadata for tables
    storage.store_metadata(
        meta_md5=hash_1,
        element=element_to_store_1,
        meta=meta_to_store_1,
    )
    storage.store_metadata(
        meta_md5=hash_2,
        element=element_to_store_2,
        meta=meta_to_store_2,
    )
    storage.store_metadata(
        meta_md5=hash_3,
        element=element_to_store_3,
        meta=meta_to_store_3,
    )

    # Store tables
    storage.store_table(
        meta_md5=hash_1,
        element=element_to_store_1,
        data=data_1,
        columns=col_headers,
        rows_col_name=row_header,
    )
    storage.store_table(
        meta_md5=hash_2,
        element=element_to_store_2,
        data=data_2,
        columns=col_headers,
        rows_col_name=row_header,
    )
    storage.store_table(
        meta_md5=hash_3,
        element=element_to_store_3,
        data=data_3,
        columns=col_headers,
        rows_col_name=row_header,
    )

    # Check that base URI does not exist yet
    assert not uri.exists()

    # Convert element to preifx
    prefix_1 = element_to_prefix(meta_1["element"])  # type: ignore
    prefix_2 = element_to_prefix(meta_2["element"])  # type: ignore
    prefix_3 = element_to_prefix(meta_3["element"])  # type: ignore

    # URIs for data storage
    uri_1 = uri.parent / f"{prefix_1}{uri.name}"
    uri_2 = uri.parent / f"{prefix_2}{uri.name}"
    uri_3 = uri.parent / f"{prefix_3}{uri.name}"

    # Check URIs for data storage exist
    assert uri_1.exists()
    assert uri_2.exists()
    assert uri_3.exists()

    # Read stored metadata from different files using element
    read_meta_1 = storage._read_metadata(element=meta_1["element"])
    read_meta_2 = storage._read_metadata(element=meta_2["element"])
    read_meta_3 = storage._read_metadata(element=meta_3["element"])

    # Check if metadata are equal
    assert read_meta_1 == read_meta_2
    assert read_meta_2 == read_meta_3

    # Collect data
    storage.collect()
    # Check that base URI exists now
    assert uri.exists()

    # Read unified metadata
    read_unified_meta = storage._read_metadata()

    # Check if aggregated metadata are equal
    assert read_unified_meta == [read_meta_1, read_meta_2, read_meta_3]
