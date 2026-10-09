"""Provide tests for storing the same data more than once."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from junifer.storage import HDF5FeatureStorage, SQLiteFeatureStorage
from junifer.storage.base import BaseFeatureStorage


# The storage types supported by each storage
_CASES = [
    (klass, kind, single_output)
    for klass, kinds in (
        (
            HDF5FeatureStorage,
            [
                "vector",
                "matrix",
                "timeseries",
                "scalar_table",
                "timeseries_2d",
            ],
        ),
        (SQLiteFeatureStorage, ["vector", "matrix", "timeseries"]),
    )
    for kind in kinds
    for single_output in (True, False)
]


def _data(kind: str, value: float) -> dict:
    """Get data of a storage type with a value.

    Parameters
    ----------
    kind : str
        The storage type.
    value : float
        The value of the data.

    Returns
    -------
    dict
        The data and the other parameters to store it.

    """
    names = {"col_names": ["a", "b"]}
    if kind == "vector":
        return {"data": np.full((1, 2), value), **names}
    if kind == "matrix":
        return {
            "data": np.full((2, 2), value),
            "row_names": ["r1", "r2"],
            "matrix_kind": "full",
            **names,
        }
    if kind == "timeseries":
        return {"data": np.full((3, 2), value), **names}
    if kind == "scalar_table":
        return {
            "data": np.full((2, 2), value),
            "row_names": ["r1", "r2"],
            "row_header_col_name": "feature",
            **names,
        }
    return {
        "data": np.full((3, 2, 2), value),
        "row_names": ["r1", "r2"],
        **names,
    }


def _store(
    storage: BaseFeatureStorage,
    kind: str,
    element: dict,
    value: float,
    element_keys: list[str] | None = None,
) -> None:
    """Store data of an element being processed, as a marker does.

    Parameters
    ----------
    storage : BaseFeatureStorage
        The storage.
    kind : str
        The storage type.
    element : dict
        The element being processed.
    value : float
        The value of the data.
    element_keys : list of str or None, optional
        The keys of the element that the data depends on. If None, all the
        keys (default None).

    """
    meta = {
        "element": element,
        "dependencies": set(),
        "marker": {"name": "test"},
        "type": "BOLD",
    }
    if element_keys is not None:
        meta["_element_keys"] = element_keys
    storage.store(kind=kind, meta=meta, **_data(kind, value))


def _read(
    storage: BaseFeatureStorage, collect: bool = True
) -> tuple[pd.DataFrame, list[tuple]]:
    """Read the stored feature, collecting it first if needed.

    Parameters
    ----------
    storage : BaseFeatureStorage
        The storage.
    collect : bool, optional
        Whether to collect the files of the elements first (default True).

    Returns
    -------
    pandas.DataFrame
        The feature.
    list of tuple
        The elements of the feature, without duplicates.

    """
    if not storage.single_output and collect:
        storage.collect()
    reader = type(storage)(uri=storage.uri)
    (md5,) = reader.list_features()
    df = reader.read_df(feature_md5=md5)
    # No repeated rows (the index has the element and, for some storage
    # types, the rows of the data of an element)
    assert not df.index.duplicated().any()
    keys = [k for k in ("subject", "task") if k in df.index.names]
    levels = [df.index.get_level_values(k) for k in keys]
    elements = sorted(set(zip(*levels, strict=True)))
    return df, elements


@pytest.mark.parametrize("klass, kind, single_output", _CASES)
def test_store_again(
    tmp_path: Path, klass: type, kind: str, single_output: bool
) -> None:
    """Test storing the same element again does not change the storage.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    klass : type
        The parametrized storage class.
    kind : str
        The parametrized storage type.
    single_output : bool
        The parametrized storage in a single file.

    """
    storage = klass(uri=tmp_path / "out.db", single_output=single_output)
    element = {"subject": "sub-01", "task": "rest"}
    _store(storage, kind, element, 1)
    # Already stored: skipped, even with other values
    _store(storage, kind, element, 2)
    df, elements = _read(storage)
    assert elements == [("sub-01", "rest")]
    assert (df.to_numpy() == 1).all()


@pytest.mark.parametrize("klass, kind, single_output", _CASES)
def test_store_element_of_data(
    tmp_path: Path, klass: type, kind: str, single_output: bool
) -> None:
    """Test storing data that does not depend on all the element keys.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    klass : type
        The parametrized storage class.
    kind : str
        The parametrized storage type.
    single_output : bool
        The parametrized storage in a single file.

    """
    storage = klass(uri=tmp_path / "out.db", single_output=single_output)
    # The data of a subject, the same when processing each of its tasks
    for task in ("rest", "movie"):
        element = {"subject": "sub-01", "task": task}
        _store(storage, kind, element, 1, element_keys=["subject"])
    if not single_output:
        # One file for each element being processed
        files = sorted(x.name for x in tmp_path.glob("*_out.db"))
        assert files == [
            "element_sub-01_movie_out.db",
            "element_sub-01_rest_out.db",
        ]
    df, elements = _read(storage)
    assert elements == [("sub-01",)]
    assert (df.to_numpy() == 1).all()


@pytest.mark.parametrize(
    "klass, kind, single_output",
    [case for case in _CASES if not case[2]],
)
def test_collect_again(
    tmp_path: Path, klass: type, kind: str, single_output: bool
) -> None:
    """Test collecting again does not change the storage.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    klass : type
        The parametrized storage class.
    kind : str
        The parametrized storage type.
    single_output : bool
        The parametrized storage in a single file.

    """
    storage = klass(uri=tmp_path / "out.db", single_output=single_output)
    for subject in ("sub-01", "sub-02"):
        _store(storage, kind, {"subject": subject, "task": "rest"}, 1)
    storage.collect()
    _, elements = _read(storage)
    assert elements == [("sub-01", "rest"), ("sub-02", "rest")]


@pytest.mark.parametrize("klass, kind, single_output", _CASES)
def test_store_trial_then_all(
    tmp_path: Path, klass: type, kind: str, single_output: bool
) -> None:
    """Test storing some elements and then all the elements.

    For example, running a few elements to test a configuration, and then
    queueing all the elements with the same configuration.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    klass : type
        The parametrized storage class.
    kind : str
        The parametrized storage type.
    single_output : bool
        The parametrized storage in a single file.

    """
    storage = klass(uri=tmp_path / "out.db", single_output=single_output)
    # Trial
    _store(storage, kind, {"subject": "sub-01", "task": "rest"}, 1)
    _read(storage)
    # All the elements
    for subject in ("sub-01", "sub-02"):
        _store(storage, kind, {"subject": subject, "task": "rest"}, 2)
    df, elements = _read(storage)
    assert elements == [("sub-01", "rest"), ("sub-02", "rest")]
    # The trial element keeps its values
    sub01 = df.xs("sub-01", level="subject")
    assert (sub01.to_numpy() == 1).all()


@pytest.mark.parametrize("klass", [HDF5FeatureStorage, SQLiteFeatureStorage])
def test_collect_several_elements(tmp_path: Path, klass: type) -> None:
    """Test collecting a file with more than one element raises an error.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    klass : type
        The parametrized storage class.

    """
    # A file with two elements, named as the file of an element
    several = klass(uri=tmp_path / "element_all_out.db")
    for subject in ("sub-01", "sub-02"):
        _store(several, "timeseries", {"subject": subject}, 1)
    storage = klass(uri=tmp_path / "out.db", single_output=False)
    with pytest.raises(RuntimeError, match="has 2 elements for the feature"):
        storage.collect()
