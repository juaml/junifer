"""Provide tests for sqlite."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import List, Union

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal
from sqlalchemy import create_engine

from junifer.storage.sqlite import SQLiteFeatureStorage
from junifer.storage.utils import (
    element_to_index,
    element_to_prefix,
    process_meta,
)


df1 = pd.DataFrame(
    {
        "element": [1, 2, 3, 4, 5],
        "pk2": ["a", "b", "c", "d", "e"],
        "col1": [11, 22, 33, 44, 55],
        "col2": [111, 222, 333, 444, 555],
    }
).set_index(["element", "pk2"])

df2 = pd.DataFrame(
    {
        "element": [2, 5, 6],
        "pk2": ["b", "e", "f"],
        "col1": [2222, 5555, 66],
        "col2": [22222, 55555, 666],
    }
).set_index(["element", "pk2"])

df_update = pd.DataFrame(
    {
        "element": [1, 2, 3, 4, 5, 6],
        "pk2": ["a", "b", "c", "d", "e", "f"],
        "col1": [11, 2222, 33, 44, 5555, 66],
        "col2": [111, 22222, 333, 444, 55555, 666],
    }
).set_index(["element", "pk2"])

df_ignore = pd.DataFrame(
    {
        "element": [1, 2, 3, 4, 5, 6],
        "pk2": ["a", "b", "c", "d", "e", "f"],
        "col1": [11, 22, 33, 44, 55, 66],
        "col2": [111, 222, 333, 444, 555, 666],
    }
).set_index(["element", "pk2"])


def _read_sql(
    table_name: str, uri: str, index_col: Union[str, List[str]]
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
    uri = tmp_path / "test_single_output.db"
    # Single storage, must be the uri
    storage = SQLiteFeatureStorage(
        uri=uri, single_output=True, upsert="ignore"
    )
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
    uri = tmp_path / "test_multi_output.db"
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
    uri = tocreate.absolute() / "test_single_output.db"
    _ = SQLiteFeatureStorage(uri=uri, single_output=True, upsert="ignore")
    # Path exists now
    assert tocreate.exists()


def test_upsert_replace(tmp_path: Path) -> None:
    """Test dataframe store with upsert=replace.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_upsert_replace.db"
    # Single storage, must be the uri
    storage = SQLiteFeatureStorage(
        uri=uri, single_output=True, upsert="ignore"
    )
    # Metadata to store
    meta = {"element": "test", "version": "0.0.1"}
    # Save to database
    storage.store_df(df=df1, meta=meta)
    # Store metadata
    table_name = storage.store_metadata(meta)
    # Read stored table
    c_df1 = _read_sql(
        table_name=table_name, uri=uri.as_posix(), index_col=["element", "pk2"]
    )
    # Check if dataframes are equal
    assert_frame_equal(df1, c_df1)
    # Upsert using replace
    storage._save_upsert(df=df2, name=table_name, if_exists="replace")
    # Read stored table
    c_df2 = _read_sql(
        table_name=table_name, uri=uri.as_posix(), index_col=["element", "pk2"]
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
    uri = tmp_path / "test_upsert_ignore.db"
    # Single storage, must be the uri
    storage = SQLiteFeatureStorage(
        uri=uri, single_output=True, upsert="ignore"
    )
    # Metadata to store
    meta = {"element": "test", "version": "0.0.1"}
    # Save to database
    storage.store_df(df=df1, meta=meta)
    # Store metadata
    table_name = storage.store_metadata(meta=meta)
    # Read stored table
    c_df1 = _read_sql(
        table_name=table_name, uri=uri.as_posix(), index_col=["element", "pk2"]
    )
    # Check if dataframes are equal
    assert_frame_equal(df1, c_df1)
    # Check for warning
    with pytest.warns(RuntimeWarning, match="are already present"):
        storage.store_df(df2, meta)
    # Read stored table
    c_dfignore = _read_sql(
        table_name, uri=uri.as_posix(), index_col=["element", "pk2"]
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
    uri = tmp_path / "test_upsert_delete.db"
    storage = SQLiteFeatureStorage(uri=uri, single_output=True)
    # Metadata to store
    meta = {"element": "test", "version": "0.0.1"}
    # Save to database
    storage.store_df(df1, meta)
    # Store metadata
    table_name = storage.store_metadata(meta)
    # Read stored table
    c_df1 = _read_sql(
        table_name=table_name, uri=uri.as_posix(), index_col=["element", "pk2"]
    )
    # Check if dataframes are equal
    assert_frame_equal(df1, c_df1)
    # Save to database
    storage.store_df(df2, meta)
    # Read stored table
    c_dfupdate = _read_sql(
        table_name, uri=uri.as_posix(), index_col=["element", "pk2"]
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
    uri = tmp_path / "test_upsert_invalid.db"
    with pytest.raises(ValueError):
        SQLiteFeatureStorage(uri=uri, single_output=True, upsert="wrong")


# TODO: can the tests be separated?
def test_store_df_and_read_df(tmp_path: Path) -> None:
    """Test storing dataframe and reading of stored table into dataframe.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_store_df_and_read_df.db"
    storage = SQLiteFeatureStorage(
        uri=uri, single_output=True, upsert="ignore"
    )
    # Metadata to store
    meta = {
        "element": "test",
        "version": "0.0.1",
        "marker": {"name": "fcname"},
    }
    # Columns to store
    to_store = df1[["col1", "col2"]]
    # Check for error while storing
    with pytest.raises(ValueError, match=r"missing index items"):
        storage.store_df(to_store.set_index("col1"), meta)
    # Set index
    to_store = df1.reset_index().set_index(["element", "pk2", "col1"])
    # Check for error while storing
    with pytest.raises(ValueError, match=r"extra items"):
        storage.store_df(to_store, meta)
    # Convert element to index
    idx = element_to_index(meta, n_rows=len(to_store))
    # Set index
    to_store = to_store.set_index(idx)
    # Store dataframe
    storage.store_df(to_store, meta)
    # Store metadata
    table_name = storage.store_metadata(meta)
    # List stored features
    features = storage.list_features()
    # Check correct usage
    assert len(features) == 1
    assert table_name.replace("meta_", "") in features
    # Check for missing feature
    with pytest.raises(ValueError, match="not found"):
        storage.read_df("wrong_md5")
    # Check for missing feature to fetch
    with pytest.raises(ValueError, match="least one"):
        storage.read_df()
    # Check for multiple features to fetch
    with pytest.raises(ValueError, match="Only one"):
        storage.read_df("wrong_md5", "wrong_name")
    # Get MD5 hash of features
    feature_md5 = list(features.keys())[0]
    # Check for key
    assert "fcname" == features[feature_md5]["name"]
    # Read into dataframes
    read_df1 = storage.read_df(feature_md5=feature_md5)
    read_df2 = storage.read_df(feature_name="fcname")
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
    uri = tmp_path / "test_metadata_store.db"
    # Single storage, must be the uri
    storage = SQLiteFeatureStorage(
        uri=uri, single_output=True, upsert="ignore"
    )
    # Metadata to store
    meta = {"element": "test", "version": "0.0.1"}
    # Store metadata
    table_name = storage.store_metadata(meta)
    assert table_name.startswith("meta_")


def test_store_table(tmp_path: Path) -> None:
    """Test table store.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_store_table.db"
    storage = SQLiteFeatureStorage(uri=uri, single_output=True)
    # Metadata to store
    meta = {"element": "test", "version": "0.0.1", "marker": {"name": "fc"}}
    # Data to store
    data = [
        [1, 10],
        [2, 20],
        [3, 30],
        [4, 40],
        [5, 50],
    ]
    # Convert element to index
    idx = element_to_index(meta, n_rows=5, rows_col_name="scan")
    # Create dataframe
    df = pd.DataFrame(data, columns=["f1", "f2"], index=idx)
    # Store table
    storage.store_table(data, meta, columns=["f1", "f2"], rows_col_name="scan")
    # Store metadata
    table_name = storage.store_metadata(meta)
    # Read stored table
    c_df = _read_sql(
        table_name=table_name,
        uri=uri.as_posix(),
        index_col=["element", "scan"],
    )
    # Check if dataframes are equal
    assert_frame_equal(df, c_df)

    # New data to store
    data_new = [[1, 10], [2, 20], [3, 300], [4, 40], [5, 50], [6, 600]]
    # Convert element to index
    idx_new = element_to_index(meta, n_rows=6, rows_col_name="scan")
    # Create dataframe
    df_new = pd.DataFrame(data_new, columns=["f1", "f2"], index=idx_new)
    # Check warning
    with pytest.warns(RuntimeWarning, match=r"Some rows"):
        storage.store_table(
            data_new, meta, columns=["f1", "f2"], rows_col_name="scan"
        )
    # Read stored table
    c_df_new = _read_sql(
        table_name=table_name,
        uri=uri.as_posix(),
        index_col=["element", "scan"],
    )
    # Check if dataframes are equal
    assert_frame_equal(df_new, c_df_new)


# TODO: can the test be parametrized?
def test_store_multiple_output(tmp_path: Path):
    """Test storing using single_output=False.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    uri = tmp_path / "test_store_multiple_output.db"
    storage = SQLiteFeatureStorage(uri=uri, single_output=False)
    # Metadata to store
    meta1 = {
        "element": {"subject": "test-01", "session": "ses-01"},
        "version": "0.0.1",
        "marker": {"name": "fc"},
    }
    meta2 = {
        "element": {"subject": "test-02", "session": "ses-01"},
        "version": "0.0.1",
        "marker": {"name": "fc"},
    }
    meta3 = {
        "element": {"subject": "test-01", "session": "ses-02"},
        "version": "0.0.1",
        "marker": {"name": "fc"},
    }
    # Data to store
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
    # Process metadata for storage
    hash1, _ = process_meta(meta1)
    # Convert element to index
    idx1 = element_to_index(meta1, n_rows=5, rows_col_name="scan")
    # Create dataframe
    df1 = pd.DataFrame(data1, columns=["f1", "f2"], index=idx1)
    # Process metadata for storage
    hash2, _ = process_meta(meta2)
    # Convert element to index
    idx2 = element_to_index(meta2, n_rows=5, rows_col_name="scan")
    # Create dataframe
    df2 = pd.DataFrame(data2, columns=["f1", "f2"], index=idx2)
    # Process metadata for storage
    hash3, _ = process_meta(meta3)
    # Convert element to index
    idx3 = element_to_index(meta3, n_rows=5, rows_col_name="scan")
    # Create dataframe
    df3 = pd.DataFrame(data3, columns=["f1", "f2"], index=idx3)
    # Check hash equality
    assert hash1 == hash2
    assert hash2 == hash3
    # Store tables
    storage.store_table(
        data1, meta1, columns=["f1", "f2"], rows_col_name="scan"
    )
    storage.store_table(
        data2, meta2, columns=["f1", "f2"], rows_col_name="scan"
    )
    storage.store_table(
        data3, meta3, columns=["f1", "f2"], rows_col_name="scan"
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
    # Store metadata
    table_name = storage.store_metadata(meta1)
    # Set index columns
    cols = ["subject", "session", "scan"]
    # Read stored tables
    cdf1 = _read_sql(table_name, uri1.as_posix(), index_col=cols)
    cdf2 = _read_sql(table_name, uri2.as_posix(), index_col=cols)
    cdf3 = _read_sql(table_name, uri3.as_posix(), index_col=cols)
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
    uri = tmp_path / "test_collect.db"
    storage = SQLiteFeatureStorage(uri=uri)
    # Metadata for storage
    meta1 = {
        "element": {"subject": "test-01", "session": "ses-01"},
        "version": "0.0.1",
        "marker": {"name": "fc"},
    }
    meta2 = {
        "element": {"subject": "test-02", "session": "ses-01"},
        "version": "0.0.1",
        "marker": {"name": "fc"},
    }
    meta3 = {
        "element": {"subject": "test-01", "session": "ses-02"},
        "version": "0.0.1",
        "marker": {"name": "fc"},
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
    storage.store_table(
        data1, meta1, columns=["f1", "f2"], rows_col_name="scan"
    )
    storage.store_table(
        data2, meta2, columns=["f1", "f2"], rows_col_name="scan"
    )
    storage.store_table(
        data3, meta3, columns=["f1", "f2"], rows_col_name="scan"
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
    cols = ["subject", "session", "scan"]
    # Store metadata
    table_name = storage.store_metadata(meta1)
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
