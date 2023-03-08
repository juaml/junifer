"""Provide tests for HDF5 storage interface."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
#          Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from itertools import product
from pathlib import Path

import numpy as np
import pytest
from numpy.testing import assert_array_equal
from pandas.testing import assert_frame_equal

from junifer.storage import HDF5FeatureStorage
from junifer.storage.utils import element_to_prefix, process_meta


def test_get_valid_inputs() -> None:
    """Test valid inputs."""
    storage = HDF5FeatureStorage(uri="/tmp")
    assert storage.get_valid_inputs() == ["matrix", "vector", "timeseries"]


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


def test_single_output_meta_not_found_error(tmp_path: Path) -> None:
    """Test single output metadata not found error.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_single_output_no_meta.hdf5"
    storage = HDF5FeatureStorage(uri=uri, single_output=True)
    # Store data to create the file
    storage._store_data(
        kind="vector",
        meta_md5="md5",
        element=[{"sub": "001"}],
        data=np.empty((1, 1)),
    )
    # Check metadata error
    with pytest.raises(IOError, match="`meta` not found in:"):
        storage._read_metadata()


def test_single_output_file_not_found_error(tmp_path: Path) -> None:
    """Test single output file not found error.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_single_output_no_file.hdf5"
    storage = HDF5FeatureStorage(uri=uri, single_output=True)
    # Check file error
    with pytest.raises(IOError, match="HDF5 file not found at:"):
        storage._read_data(md5="md5")


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


def test_store_data_ignore_duplicate(tmp_path: Path) -> None:
    """Test duplicate ignore for data store.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_duplicate_data_store.hdf5"
    # Single storage, must be the uri
    storage = HDF5FeatureStorage(uri=uri, single_output=True)
    # Store data first time
    storage._store_data(
        kind="vector",
        meta_md5="md5",
        element=[{"sub": "001"}],
        data=np.empty((1, 1)),
    )
    # Store data second time, should be ignored
    storage._store_data(
        kind="vector",
        meta_md5="md5",
        element=[{"sub": "001"}],
        data=np.empty((1, 1)),
    )


def test_store_data_incorrect_kwargs(tmp_path: Path) -> None:
    """Test incorrect kwargs for data store.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_incorrect_kwargs_data_store.hdf5"
    # Single storage, must be the uri
    storage = HDF5FeatureStorage(uri=uri, single_output=True)
    # Store data first time
    storage._store_data(
        kind="vector",
        meta_md5="md5",
        element=[{"sub": "001"}],
        data=np.empty((1, 1)),
    )
    # Store data second time, should be ignored
    with pytest.raises(RuntimeError, match="The additional data for"):
        storage._store_data(
            kind="vector",
            meta_md5="md5",
            element=[{"sub": "001"}],
            data=np.empty((1, 1)),
            col_names="col",
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
    assert read_df.columns.to_list() == list(product(row_headers, col_headers))

    # Diagonal validation error
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
    # Matrix kind and shape validation
    with pytest.raises(ValueError, match="non-square"):
        storage.store_matrix(
            meta_md5=meta_md5,
            element=element_to_store,
            data=data,
            row_names=row_headers,
            col_names=col_headers,
            matrix_kind="triu",
        )
    # Matrix kind validation
    with pytest.raises(ValueError, match="Invalid kind"):
        storage.store_matrix(
            meta_md5=meta_md5,
            element=element_to_store,
            data=data,
            row_names=row_headers,
            col_names=col_headers,
            matrix_kind="wrong",
        )
    # Row data and label validation
    with pytest.raises(ValueError, match="of row names"):
        storage.store_matrix(
            meta_md5=meta_md5,
            element=element_to_store,
            data=data,
            row_names=["row1", "row2", "row3"],
            col_names=col_headers,
            matrix_kind="full",
        )
    # Column data and label validation
    with pytest.raises(ValueError, match="of column names"):
        storage.store_matrix(
            meta_md5=meta_md5,
            element=element_to_store,
            data=data,
            row_names=row_headers,
            col_names=["col1", "col2", "col3", "col4"],
            matrix_kind="full",
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
    # Check the MD5
    assert "BOLD_fc" == features[meta_md5]["name"]

    # Read the dataframe
    read_df = storage.read_df(feature_md5=meta_md5)
    # Check shape of dataframe
    assert read_df.shape == (1, 12)
    # Check data of dataframe
    assert_array_equal(read_df.values, data.reshape(1, -1))
    # Check column headers
    assert read_df.columns.to_list() == list(product(["r0", "r1", "r2", "r3"], ["c0", "c1", "c2"]))


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
    assert_array_equal(read_df.values, data.reshape(1, -1))
    # Check column headers
    assert read_df.columns.to_list() == list(product(row_headers, col_headers))


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
    assert_array_equal(read_df.values, data.reshape(1, -1))
    # Check column headers
    assert read_df.columns.to_list() == list(product(row_headers, col_headers))


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
    assert_array_equal(read_df.values, data.reshape(1, -1))
    # Check column headers
    assert read_df.columns.to_list() == list(product(row_headers, col_headers))


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
    assert_array_equal(read_df.values, data.reshape(1, -1))
    # Check column headers
    assert read_df.columns.to_list() == list(product(row_headers, col_headers))


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

    # Store vector
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
    data_1 = np.array([10, 20, 30, 40, 50])
    data_2 = data_1 * 10
    data_3 = data_1 * 20
    col_headers = ["f1", "f2", "f3", "f4", "f5"]

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
    storage.store_vector(
        meta_md5=hash_1,
        element=element_to_store_1,
        data=data_1,
        col_names=col_headers,
    )
    storage.store_vector(
        meta_md5=hash_2,
        element=element_to_store_2,
        data=data_2,
        col_names=col_headers,
    )
    storage.store_vector(
        meta_md5=hash_3,
        element=element_to_store_3,
        data=data_3,
        col_names=col_headers,
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
    read_unified_meta = storage.list_features()

    # Check if aggregated metadata are equal
    assert read_unified_meta == {**read_meta_1, **read_meta_2, **read_meta_3}


def test_collect_error_single_output() -> None:
    """Test error for collect in single output storage."""
    with pytest.raises(
        NotImplementedError,
        match="is not implemented for single output.",
    ):
        storage = HDF5FeatureStorage(uri="/tmp", single_output=True)
        storage.collect()
