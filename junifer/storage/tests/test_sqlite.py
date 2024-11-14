"""Provide tests for SQLite storage interface."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import Union

import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_array_equal
from pandas.testing import assert_frame_equal
from sqlalchemy import create_engine

from junifer.storage.sqlite import SQLiteFeatureStorage
from junifer.storage.utils import element_to_prefix, process_meta


df1 = pd.DataFrame(
    {
        "subject": [1, 2, 3, 4, 5],
        "pk2": ["a", "b", "c", "d", "e"],
        "col1": [11, 22, 33, 44, 55],
        "col2": [111, 222, 333, 444, 555],
    }
).set_index(["subject", "pk2"])

df2 = pd.DataFrame(
    {
        "subject": [2, 5, 6],
        "pk2": ["b", "e", "f"],
        "col1": [2222, 5555, 66],
        "col2": [22222, 55555, 666],
    }
).set_index(["subject", "pk2"])

df_update = pd.DataFrame(
    {
        "subject": [1, 2, 3, 4, 5, 6],
        "pk2": ["a", "b", "c", "d", "e", "f"],
        "col1": [11, 2222, 33, 44, 5555, 66],
        "col2": [111, 22222, 333, 444, 55555, 666],
    }
).set_index(["subject", "pk2"])

df_ignore = pd.DataFrame(
    {
        "subject": [1, 2, 3, 4, 5, 6],
        "pk2": ["a", "b", "c", "d", "e", "f"],
        "col1": [11, 22, 33, 44, 55, 66],
        "col2": [111, 222, 333, 444, 555, 666],
    }
).set_index(["subject", "pk2"])


def _read_sql(
    table_name: str, uri: str, index_col: Union[str, list[str]]
) -> pd.DataFrame:
    """Read database table into a pandas DataFrame.

    Parameters
    ----------
    table_name : str
         The table name.
    uri : str
         The URI of the database.
    index_col : str
         The index column name.

    Returns
    -------
    pandas.DataFrame
        The contents of the table in a DataFrame.

    """
    engine = create_engine(f"sqlite:///{uri}", echo=False)
    df = pd.read_sql(sql=table_name, con=engine, index_col=index_col)
    return df


def test_get_engine_single_output(tmp_path: Path) -> None:
    """Test engine retrieval with single output.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_single_output.sqlite"
    # Single storage, must be the uri
    storage = SQLiteFeatureStorage(uri=uri, upsert="ignore")
    assert storage.single_output is True
    engine = storage.get_engine()
    assert engine.url.drivername == "sqlite"
    assert engine.url.database == str(uri.absolute())


def test_get_engine_multi_output(tmp_path: Path) -> None:
    """Test engine retrieval with multi output.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_multi_output.sqlite"
    storage = SQLiteFeatureStorage(
        uri=uri, single_output=False, upsert="ignore"
    )
    with pytest.raises(ValueError, match="element must be specified"):
        storage.get_engine()


def test_get_engine_single_output_creation(tmp_path: Path) -> None:
    """Test engine retrieval with single output creation.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    tocreate = tmp_path / "tocreate"
    # Path does not exist yet
    assert not tocreate.exists()
    uri = tocreate.absolute() / "test_single_output.sqlite"
    _ = SQLiteFeatureStorage(uri=uri, upsert="ignore")
    # Path exists now
    assert tocreate.exists()


def test_upsert_replace(tmp_path: Path) -> None:
    """Test dataframe store with upsert=replace.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_upsert_replace.sqlite"
    # Single storage, must be the uri
    storage = SQLiteFeatureStorage(uri=uri, upsert="ignore")
    # Save to database
    storage.store_df(
        meta_md5="table_name", element={"subject": "test"}, df=df1
    )
    table_name = "meta_table_name"
    # Read stored table
    c_df1 = _read_sql(
        table_name=table_name, uri=uri.as_posix(), index_col=["subject", "pk2"]
    )
    # Check if dataframes are equal
    assert_frame_equal(df1, c_df1)
    # Upsert using replace
    storage._save_upsert(df=df2, name=table_name, if_exists="replace")
    # Read stored table
    c_df2 = _read_sql(
        table_name=table_name, uri=uri.as_posix(), index_col=["subject", "pk2"]
    )
    # Check if dataframes are equal
    assert_frame_equal(df2, c_df2)


def test_upsert_ignore(tmp_path: Path) -> None:
    """Test dataframe store with upsert=ignore.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_upsert_ignore.sqlite"
    # Single storage, must be the uri
    storage = SQLiteFeatureStorage(uri=uri, upsert="ignore")
    # Save to database
    storage.store_df(
        meta_md5="table_name", element={"subject": "test"}, df=df1
    )
    table_name = "meta_table_name"
    # Read stored table
    c_df1 = _read_sql(
        table_name=table_name, uri=uri.as_posix(), index_col=["subject", "pk2"]
    )
    # Check if dataframes are equal
    assert_frame_equal(df1, c_df1)
    # Check for warning
    with pytest.warns(RuntimeWarning, match="are already present"):
        storage.store_df(
            meta_md5="table_name", element={"subject": "test"}, df=df2
        )
    # Read stored table
    c_dfignore = _read_sql(
        table_name, uri=uri.as_posix(), index_col=["subject", "pk2"]
    )
    # Check if dataframes are equal
    assert_frame_equal(c_dfignore, df_ignore)
    # Check for error
    with pytest.raises(ValueError, match=r"already exists"):
        storage._save_upsert(df2, table_name, if_exists="fail")


def test_upsert_update(tmp_path: Path) -> None:
    """Test dataframe store with upsert=delete.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_upsert_delete.sqlite"
    storage = SQLiteFeatureStorage(uri=uri)
    # Save to database
    storage.store_df(
        meta_md5="table_name", element={"subject": "test"}, df=df1
    )
    table_name = "meta_table_name"
    # Read stored table
    c_df1 = _read_sql(
        table_name=table_name, uri=uri.as_posix(), index_col=["subject", "pk2"]
    )
    # Check if dataframes are equal
    assert_frame_equal(df1, c_df1)
    # Save to database
    storage.store_df(
        meta_md5="table_name", element={"subject": "test"}, df=df2
    )
    # Read stored table
    c_dfupdate = _read_sql(
        table_name, uri=uri.as_posix(), index_col=["subject", "pk2"]
    )
    # Check if dataframes are equal
    assert_frame_equal(c_dfupdate, df_update)


def test_upsert_invalid_option(tmp_path: Path) -> None:
    """Test dataframe store with invalid option for upsert.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_upsert_invalid.sqlite"
    with pytest.raises(ValueError):
        SQLiteFeatureStorage(uri=uri, upsert="wrong")


def test_read(tmp_path: Path) -> None:
    """Test reading of stored feature.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_read.sqlite"
    storage = SQLiteFeatureStorage(uri=uri, upsert="ignore")
    # Check error
    with pytest.raises(NotImplementedError):
        storage.read()


# TODO: can the tests be separated?
def test_store_df_and_read_df(tmp_path: Path) -> None:
    """Test storing dataframe and reading of stored table into dataframe.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_store_df_and_read_df.sqlite"
    storage = SQLiteFeatureStorage(uri=uri, upsert="ignore")
    # Metadata to store
    meta_md5 = "feature_md5"
    element = {"subject": "test"}
    meta = {
        "element": element,
        "dependencies": ["numpy"],
        "marker": {
            "name": "markername",
        },
        "type": "BOLD",
    }

    _, meta_to_store, element_to_store = process_meta(meta)
    # Store metadata
    storage.store_metadata(
        meta_md5="feature_md5", element=element_to_store, meta=meta_to_store
    )

    # Columns to store
    to_store = df1[["col1", "col2"]]
    # Check for error while storing
    with pytest.raises(ValueError, match=r"missing index items"):
        storage.store_df(
            meta_md5=meta_md5, element=element, df=to_store.set_index("col1")
        )
    # Set index
    to_store = df1.reset_index().set_index(["subject", "pk2", "col1"])
    # Check for error while storing
    with pytest.raises(ValueError, match=r"extra items"):
        storage.store_df(meta_md5=meta_md5, element=element, df=to_store)
    # Convert element to index
    idx = storage.element_to_index(element=element, n_rows=len(to_store))
    # Set index
    to_store = to_store.set_index(idx)
    # Store dataframe
    storage.store_df(meta_md5=meta_md5, element=element, df=to_store)

    # List stored features
    features = storage.list_features()
    # Check correct usage
    assert len(features) == 1
    assert "feature_md5" in features
    # Check for missing feature
    with pytest.raises(ValueError, match="not found"):
        storage.read_df(feature_md5="wrong_md5")
    with pytest.raises(ValueError, match="not found"):
        storage.read_df(feature_name="wrong_name")
    # Check for missing feature to fetch
    with pytest.raises(ValueError, match="least one"):
        storage.read_df()
    # Check for multiple features to fetch
    with pytest.raises(ValueError, match="Only one"):
        storage.read_df(feature_name="wrong_name", feature_md5="wrong_md5")
    # Get MD5 hash of features
    feature_md5 = next(iter(features.keys()))
    assert "feature_md5" == feature_md5
    # Check for key
    assert "BOLD_markername" == features[feature_md5]["name"]
    # Read into dataframes
    read_df1 = storage.read_df(feature_md5=feature_md5)
    read_df2 = storage.read_df(feature_name="BOLD_markername")
    # Check if dataframes are equal
    assert_frame_equal(read_df1, read_df2)
    assert_frame_equal(read_df1, to_store)


def test_store_metadata(tmp_path: Path) -> None:
    """Test metadata store.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_metadata_store.sqlite"
    # Single storage, must be the uri
    storage = SQLiteFeatureStorage(uri=uri, upsert="ignore")
    # Metadata to store
    meta = {
        "element": {"subject": "test"},
        "dependencies": ["numpy"],
        "marker": {"name": "test"},
        "type": "BOLD",
    }

    meta_md5, meta_to_store, element_to_store = process_meta(meta)
    # Store metadata
    storage.store_metadata(
        meta_md5=meta_md5, element=element_to_store, meta=meta_to_store
    )
    features = storage.list_features()
    feature_md5 = next(iter(features.keys()))
    assert meta_md5 == feature_md5


def test_store_vector(tmp_path: Path) -> None:
    """Test vector store.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_store_vector.sqlite"
    storage = SQLiteFeatureStorage(uri=uri)
    # Metadata to store
    element = {"subject": "test"}
    dependencies = ["numpy"]
    meta = {
        "element": element,
        "dependencies": dependencies,
        "marker": {"name": "fc"},
        "type": "BOLD",
    }

    meta_md5, meta_to_store, element_to_store = process_meta(meta)
    # Store metadata
    storage.store_metadata(
        meta_md5=meta_md5, element=element_to_store, meta=meta_to_store
    )

    # Data to store
    data = [[10, 20, 30, 40, 50]]
    col_names = ["f1", "f2", "f3", "f4", "f5"]
    # Convert element to index
    idx = storage.element_to_index(element=element)
    # Create dataframe
    df = pd.DataFrame(data=data, columns=col_names, index=idx)

    # Store table
    storage.store_vector(
        meta_md5=meta_md5,
        element=element_to_store,
        data=data,
        col_names=col_names,
    )
    # Read stored table
    c_df = _read_sql(
        table_name=f"meta_{meta_md5}",
        uri=uri.as_posix(),
        index_col=["subject"],
    )
    # Check if dataframes are equal
    assert_frame_equal(df, c_df)


def test_store_matrix(tmp_path: Path) -> None:
    """Test matrix store.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_store_matrix.sqlite"
    storage = SQLiteFeatureStorage(uri=uri)
    # Metadata to store
    element = {"subject": "test"}
    dependencies = ["numpy"]
    meta = {
        "element": element,
        "dependencies": dependencies,
        "marker": {"name": "fc"},
        "type": "BOLD",
    }

    meta_md5, meta_to_store, element_to_store = process_meta(meta)
    # Store metadata
    storage.store_metadata(
        meta_md5=meta_md5, element=element_to_store, meta=meta_to_store
    )

    # Store 4 x 3 full matrix
    data = np.array(
        [[1, 2, 3], [11, 22, 33], [111, 222, 333], [1111, 2222, 3333]]
    )
    row_names = ["row1", "row2", "row3", "row4"]
    col_names = ["col1", "col2", "col3"]

    # Store matrix
    storage.store_matrix(
        meta_md5=meta_md5,
        element=element_to_store,
        data=data,
        row_names=row_names,
        col_names=col_names,
    )
    stored_names = [f"{i}~{j}" for i in row_names for j in col_names]

    features = storage.list_features()
    feature_md5 = next(iter(features.keys()))
    assert "BOLD_fc" == features[feature_md5]["name"]

    read_df = storage.read_df(feature_md5=feature_md5)
    assert read_df.shape == (1, 12)
    assert_array_equal(read_df.values[0], data.flatten())
    assert list(read_df.columns) == stored_names
    # Store without row and column names
    uri = tmp_path / "test_store_matrix_nonames.sqlite"
    storage = SQLiteFeatureStorage(uri=uri)
    # Store metadata
    storage.store_metadata(
        meta_md5=meta_md5, element=element_to_store, meta=meta_to_store
    )
    # Store matrix
    storage.store_matrix(
        meta_md5=meta_md5, element=element_to_store, data=data
    )
    stored_names = [
        f"r{i}~c{j}"
        for i in range(data.shape[0])
        for j in range(data.shape[1])
    ]
    features = storage.list_features()
    feature_md5 = next(iter(features.keys()))
    assert "BOLD_fc" == features[feature_md5]["name"]
    read_df = storage.read_df(feature_md5=feature_md5)
    assert list(read_df.columns) == stored_names

    with pytest.raises(ValueError, match="Invalid kind"):
        storage.store_matrix(
            meta_md5=meta_md5,
            element=element_to_store,
            data=data,
            row_names=row_names,
            col_names=col_names,
            matrix_kind="wrong",
        )

    with pytest.raises(ValueError, match="non-square"):
        storage.store_matrix(
            meta_md5=meta_md5,
            element=element_to_store,
            data=data,
            row_names=row_names,
            col_names=col_names,
            matrix_kind="triu",
        )

    with pytest.raises(ValueError, match="cannot be False"):
        storage.store_matrix(
            meta_md5=meta_md5,
            element=element_to_store,
            data=data,
            row_names=row_names,
            col_names=col_names,
            matrix_kind="full",
            diagonal=False,
        )

    # Store upper triangular matrix
    data = np.array([[1, 2, 3], [11, 22, 33], [111, 222, 333]])
    row_names = ["row1", "row2", "row3"]
    col_names = ["col1", "col2", "col3"]
    uri = tmp_path / "test_store_matrix_triu.sqlite"
    storage = SQLiteFeatureStorage(uri=uri)
    # Store metadata
    storage.store_metadata(
        meta_md5=meta_md5, element=element_to_store, meta=meta_to_store
    )
    storage.store_matrix(
        meta_md5=meta_md5,
        element=element_to_store,
        data=data,
        row_names=row_names,
        col_names=col_names,
        matrix_kind="triu",
    )

    stored_names = [
        "row1~col1",
        "row1~col2",
        "row1~col3",
        "row2~col2",
        "row2~col3",
        "row3~col3",
    ]

    features = storage.list_features()
    feature_md5 = next(iter(features.keys()))
    assert "BOLD_fc" == features[feature_md5]["name"]
    read_df = storage.read_df(feature_md5=feature_md5)
    assert list(read_df.columns) == stored_names
    assert_array_equal(
        read_df.values, data[np.triu_indices(n=data.shape[0])][None, :]
    )

    # Store upper triangular matrix without diagonal
    uri = tmp_path / "test_store_matrix_triu_nodiagonal.sqlite"
    storage = SQLiteFeatureStorage(uri=uri)
    # Store metadata
    storage.store_metadata(
        meta_md5=meta_md5, element=element_to_store, meta=meta_to_store
    )
    storage.store_matrix(
        meta_md5=meta_md5,
        element=element_to_store,
        data=data,
        row_names=row_names,
        col_names=col_names,
        matrix_kind="triu",
        diagonal=False,
    )

    stored_names = [
        "row1~col2",
        "row1~col3",
        "row2~col3",
    ]

    features = storage.list_features()
    feature_md5 = next(iter(features.keys()))
    assert "BOLD_fc" == features[feature_md5]["name"]
    read_df = storage.read_df(feature_md5=feature_md5)
    assert list(read_df.columns) == stored_names
    assert_array_equal(
        read_df.values, data[np.triu_indices(n=data.shape[0], k=1)][None, :]
    )

    # Store lower triangular matrix
    data = np.array([[1, 2, 3], [11, 22, 33], [111, 222, 333]])
    row_names = ["row1", "row2", "row3"]
    col_names = ["col1", "col2", "col3"]
    uri = tmp_path / "test_store_matrix_tril.sqlite"
    storage = SQLiteFeatureStorage(uri=uri)
    # Store metadata
    storage.store_metadata(
        meta_md5=meta_md5, element=element_to_store, meta=meta_to_store
    )
    storage.store_matrix(
        meta_md5=meta_md5,
        element=element_to_store,
        data=data,
        row_names=row_names,
        col_names=col_names,
        matrix_kind="tril",
    )

    stored_names = [
        "row1~col1",
        "row2~col1",
        "row2~col2",
        "row3~col1",
        "row3~col2",
        "row3~col3",
    ]

    features = storage.list_features()
    feature_md5 = next(iter(features.keys()))
    assert "BOLD_fc" == features[feature_md5]["name"]
    read_df = storage.read_df(feature_md5=feature_md5)
    assert list(read_df.columns) == stored_names
    assert_array_equal(
        read_df.values, data[np.tril_indices(n=data.shape[0])][None, :]
    )

    # Store lower triangular matrix without diagonal
    uri = tmp_path / "test_store_matrix_tril_nodiagonal.sqlite"
    storage = SQLiteFeatureStorage(uri=uri)
    # Store metadata
    storage.store_metadata(
        meta_md5=meta_md5, element=element_to_store, meta=meta_to_store
    )
    storage.store_matrix(
        meta_md5=meta_md5,
        element=element_to_store,
        data=data,
        row_names=row_names,
        col_names=col_names,
        matrix_kind="tril",
        diagonal=False,
    )
    stored_names = [
        "row2~col1",
        "row3~col1",
        "row3~col2",
    ]

    features = storage.list_features()
    feature_md5 = next(iter(features.keys()))
    assert "BOLD_fc" == features[feature_md5]["name"]
    read_df = storage.read_df(feature_md5=feature_md5)
    assert list(read_df.columns) == stored_names
    assert_array_equal(
        read_df.values, data[np.tril_indices(n=data.shape[0], k=-1)][None, :]
    )


def test_store_timeseries(tmp_path: Path) -> None:
    """Test timeseries store.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_store_timeseries.sqlite"
    storage = SQLiteFeatureStorage(uri=uri)
    # Metadata to store
    element = {"subject": "test"}
    dependencies = ["numpy"]
    meta = {
        "element": element,
        "dependencies": dependencies,
        "marker": {"name": "fc"},
        "type": "BOLD",
    }

    meta_md5, meta_to_store, element_to_store = process_meta(meta)
    # Store metadata
    storage.store_metadata(
        meta_md5=meta_md5, element=element_to_store, meta=meta_to_store
    )

    # Data to store
    data = np.array([[10], [20], [30], [40], [50]])
    col_names = ["signal"]
    # Convert element to index
    idx = storage.element_to_index(
        element=element, n_rows=5, rows_col_name="timepoint"
    )
    # Create dataframe
    df = pd.DataFrame(data=data, columns=col_names, index=idx)

    # Store table
    storage.store_timeseries(
        meta_md5=meta_md5,
        element=element_to_store,
        data=data,
        col_names=col_names,
    )
    # Read stored table
    c_df = _read_sql(
        table_name=f"meta_{meta_md5}",
        uri=uri.as_posix(),
        index_col=["subject", "timepoint"],
    )
    # Check if dataframes are equal
    assert_frame_equal(df, c_df)


# TODO: can the test be parametrized?
def test_store_multiple_output(tmp_path: Path):
    """Test storing using single_output=False.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_store_multiple_output.sqlite"
    storage = SQLiteFeatureStorage(uri=uri, single_output=False)
    # Metadata to store
    meta1 = {
        "element": {"subject": "test-01", "session": "ses-01"},
        "dependencies": ["numpy"],
        "marker": {"name": "fc"},
        "type": "BOLD",
    }
    meta2 = {
        "element": {"subject": "test-02", "session": "ses-01"},
        "dependencies": ["numpy"],
        "marker": {"name": "fc"},
        "type": "BOLD",
    }
    meta3 = {
        "element": {"subject": "test-01", "session": "ses-02"},
        "dependencies": ["numpy"],
        "marker": {"name": "fc"},
        "type": "BOLD",
    }
    # Data to store
    data1 = np.array([[10, 20, 30, 40, 50]])
    data2 = data1 * 10
    data3 = data1 * 20
    col_names = ["f1", "f2", "f3", "f4", "f5"]
    # Process metadata for storage
    hash1, meta_to_store1, element_to_store1 = process_meta(meta1)
    # Convert element to index
    idx1 = storage.element_to_index(element=element_to_store1)
    # Create dataframe
    df1 = pd.DataFrame(data1, columns=col_names, index=idx1)
    # Process metadata for storage
    hash2, meta_to_store2, element_to_store2 = process_meta(meta2)
    # Convert element to index
    idx2 = storage.element_to_index(element=element_to_store2)
    # Create dataframe
    df2 = pd.DataFrame(data2, columns=col_names, index=idx2)
    # Process metadata for storage
    hash3, meta_to_store3, element_to_store3 = process_meta(meta3)
    # Convert element to index
    idx3 = storage.element_to_index(element=element_to_store3)
    # Create dataframe
    df3 = pd.DataFrame(data3, columns=col_names, index=idx3)
    # Check hash equality
    assert hash1 == hash2
    assert hash2 == hash3
    # Store tables
    storage.store_metadata(
        meta_md5=hash1, element=element_to_store1, meta=meta_to_store1
    )
    storage.store_metadata(
        meta_md5=hash2, element=element_to_store2, meta=meta_to_store2
    )
    storage.store_metadata(
        meta_md5=hash3, element=element_to_store3, meta=meta_to_store3
    )
    storage.store_vector(
        meta_md5=hash1,
        element=element_to_store1,
        data=data1,
        col_names=col_names,
    )
    storage.store_vector(
        meta_md5=hash2,
        element=element_to_store2,
        data=data2,
        col_names=col_names,
    )
    storage.store_vector(
        meta_md5=hash3,
        element=element_to_store3,
        data=data3,
        col_names=col_names,
    )
    # Check that URI does not exist yet
    assert not uri.exists()
    # Convert element to preifx
    prefix1 = element_to_prefix(meta1["element"])
    prefix2 = element_to_prefix(meta2["element"])
    prefix3 = element_to_prefix(meta3["element"])
    # URIs for data storage
    uri1 = uri.parent / f"{prefix1}{uri.name}"
    uri2 = uri.parent / f"{prefix2}{uri.name}"
    uri3 = uri.parent / f"{prefix3}{uri.name}"
    # Check URIs for data storage exist
    assert uri1.exists()
    assert uri2.exists()
    assert uri3.exists()
    # Set index columns
    idx_cols = ["subject", "session"]
    table_name = f"meta_{hash1}"
    # Read stored tables
    cdf1 = _read_sql(table_name, uri1.as_posix(), index_col=idx_cols)
    cdf2 = _read_sql(table_name, uri2.as_posix(), index_col=idx_cols)
    cdf3 = _read_sql(table_name, uri3.as_posix(), index_col=idx_cols)
    # Check if dataframes are equal
    assert_frame_equal(df1, cdf1)
    assert_frame_equal(df2, cdf2)
    assert_frame_equal(df3, cdf3)


# TODO: can test be paramtrized?
def test_collect(tmp_path: Path) -> None:
    """Test collect.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_collect.sqlite"
    storage = SQLiteFeatureStorage(uri=uri, single_output=False)
    # Metadata for storage
    meta1 = {
        "element": {"subject": "test-01", "session": "ses-01"},
        "dependencies": ["numpy"],
        "marker": {"name": "fc"},
        "type": "BOLD",
    }
    meta2 = {
        "element": {"subject": "test-02", "session": "ses-01"},
        "dependencies": ["numpy"],
        "marker": {"name": "fc"},
        "type": "BOLD",
    }
    meta3 = {
        "element": {"subject": "test-01", "session": "ses-02"},
        "dependencies": ["numpy"],
        "marker": {"name": "fc"},
        "type": "BOLD",
    }
    # Data for storage
    data1 = np.array(
        [
            [1, 10],
            [2, 20],
            [3, 30],
            [4, 40],
            [5, 50],
        ]
    )
    data2 = data1 * 10
    data3 = data1 * 20
    # Store tables
    hash1, meta_to_store1, element_to_store1 = process_meta(meta1)
    hash2, meta_to_store2, element_to_store2 = process_meta(meta2)
    hash3, meta_to_store3, element_to_store3 = process_meta(meta3)
    storage.store_metadata(
        meta_md5=hash1, element=element_to_store1, meta=meta_to_store1
    )
    storage.store_metadata(
        meta_md5=hash2, element=element_to_store2, meta=meta_to_store2
    )
    storage.store_metadata(
        meta_md5=hash3, element=element_to_store3, meta=meta_to_store3
    )
    storage.store_vector(
        meta_md5=hash1,
        element=element_to_store1,
        data=data1,
        col_names=["f1", "f2"],
    )
    storage.store_vector(
        meta_md5=hash2,
        element=element_to_store2,
        data=data2,
        col_names=["f1", "f2"],
    )
    storage.store_vector(
        meta_md5=hash3,
        element=element_to_store3,
        data=data3,
        col_names=["f1", "f2"],
    )
    # Convert element to prefix
    prefix1 = element_to_prefix(meta1["element"])
    prefix2 = element_to_prefix(meta2["element"])
    prefix3 = element_to_prefix(meta3["element"])
    # URIs for data storage
    uri1 = uri.parent / f"{prefix1}{uri.name}"
    uri2 = uri.parent / f"{prefix2}{uri.name}"
    uri3 = uri.parent / f"{prefix3}{uri.name}"
    # Check URIs for data storage exist
    assert uri1.exists()
    assert uri2.exists()
    assert uri3.exists()
    # Check that URI does not exist yet
    assert not uri.exists()
    # Collect data
    storage.collect()
    # Check that URI exists now
    assert uri.exists()
    # Set index columns
    cols = ["subject", "session"]
    # Store metadata
    table_name = f"meta_{hash1}"
    # Read stored tables
    all_df = _read_sql(table_name, uri.as_posix(), index_col=cols)
    cdf1 = _read_sql(table_name, uri1.as_posix(), index_col=cols)
    cdf2 = _read_sql(table_name, uri2.as_posix(), index_col=cols)
    cdf3 = _read_sql(table_name, uri3.as_posix(), index_col=cols)
    # Operate on retrieved tables
    all_cdf = pd.concat([cdf1, cdf2, cdf3])
    all_df.sort_index(level=cols, inplace=True)
    all_cdf.sort_index(level=cols, inplace=True)
    # Check if dataframes are equal
    assert_frame_equal(all_df, all_cdf)
