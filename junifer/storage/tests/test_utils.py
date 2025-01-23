"""Provide tests for utils."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from collections.abc import Iterable
from typing import Union

import numpy as np
import pytest
from numpy.testing import assert_array_equal

from junifer.storage.utils import (
    element_to_prefix,
    get_dependency_version,
    matrix_to_vector,
    process_meta,
    store_matrix_checks,
    timeseries2d_to_vector,
)


@pytest.mark.parametrize(
    "dependency, max_version",
    [
        ("click", "8.2"),
        ("numpy", "1.27"),
        ("datalad", "0.20"),
        ("pandas", "2.2"),
        ("nibabel", "5.11"),
        ("nilearn", "0.11.0"),
        ("sqlalchemy", "2.1.0"),
        ("ruamel.yaml", "0.18.0"),
    ],
)
def test_get_dependency_version(dependency: str, max_version: str) -> None:
    """Test dependency resolution for installed dependencies.

    Parameters
    ----------
    dependency : str
        The parametrized dependency name.
    max_version : str
        The parametrized maximum version of the dependency.

    """
    version = get_dependency_version(dependency)
    if len(version.split(".")) == 3:  # semver
        assert int(version.split(".")[1]) <= int(max_version.split(".")[1])
    else:
        assert version < max_version


def test_get_dependency_version_invalid() -> None:
    """Test invalid package name handling for dependency resolution."""
    with pytest.raises(ValueError, match="Could not obtain"):
        get_dependency_version("foobar")


def test_process_meta_invalid_metadata_type() -> None:
    """Test invalid metadata type check for metadata hash processing."""
    meta = None
    with pytest.raises(ValueError, match=r"`meta` must be a dict"):
        process_meta(meta)  # type: ignore


# TODO: parameterize
def test_process_meta_hash() -> None:
    """Test metadata hash processing."""
    meta = {
        "element": {"foo": "bar"},
        "A": 1,
        "B": [2, 3, 4, 5, 6],
        "dependencies": ["numpy"],
        "marker": {"name": "fc"},
        "type": "BOLD",
    }
    hash1, _, element1 = process_meta(meta)
    assert element1 == {"foo": "bar"}

    meta = {
        "element": {"foo": "baz"},
        "B": [2, 3, 4, 5, 6],
        "A": 1,
        "dependencies": ["numpy"],
        "marker": {"name": "fc"},
        "type": "BOLD",
    }
    hash2, _, element2 = process_meta(meta)
    assert hash1 == hash2
    assert element2 == {"foo": "baz"}

    meta = {
        "element": {"foo": "bar"},
        "A": 1,
        "B": [2, 3, 1, 5, 6],
        "dependencies": ["numpy"],
        "marker": {"name": "fc"},
        "type": "BOLD",
    }
    hash3, _, element3 = process_meta(meta)
    assert hash1 != hash3
    assert element3 == element1

    meta4 = {
        "element": {"foo": "bar"},
        "B": {
            "B2": [2, 3, 4, 5, 6],
            "B1": [9.22, 3.14, 1.41, 5.67, 6.28],
            "B3": (1, "car"),
        },
        "A": 1,
        "dependencies": ["numpy"],
        "marker": {"name": "fc"},
        "type": "BOLD",
    }

    meta5 = {
        "A": 1,
        "B": {
            "B3": (1, "car"),
            "B1": [9.22, 3.14, 1.41, 5.67, 6.28],
            "B2": [2, 3, 4, 5, 6],
        },
        "element": {"foo": "baz"},
        "dependencies": ["numpy"],
        "marker": {"name": "fc"},
        "type": "BOLD",
    }

    hash4, _, _ = process_meta(meta4)
    hash5, _, _ = process_meta(meta5)
    assert hash4 == hash5

    # Different element keys should give a different hash
    meta6 = {
        "A": 1,
        "B": {
            "B3": (1, "car"),
            "B1": [9.22, 3.14, 1.41, 5.67, 6.28],
            "B2": [2, 3, 4, 5, 6],
        },
        "element": {"bar": "baz"},
        "dependencies": ["numpy"],
        "marker": {"name": "fc"},
        "type": "BOLD",
    }
    hash6, _, _ = process_meta(meta6)
    assert hash4 != hash6


def test_process_meta_invalid_metadata_key() -> None:
    """Test invalid metadata key check for metadata hash processing."""
    meta = {}
    with pytest.raises(ValueError, match=r"element"):
        process_meta(meta)

    meta = {"element": {}}
    with pytest.raises(ValueError, match=r"marker"):
        process_meta(meta)

    meta = {"element": {}, "marker": {}}
    with pytest.raises(ValueError, match=r"key 'name'"):
        process_meta(meta)

    meta = {"element": {}, "marker": {"name": "test"}}
    with pytest.raises(ValueError, match=r"key 'type'"):
        process_meta(meta)

    meta = {"element": {}, "marker": {"name": "test"}, "type": "BOLD"}
    with pytest.raises(ValueError, match=r"dependencies"):
        process_meta(meta)


@pytest.mark.parametrize(
    "meta,elements",
    [
        (
            {
                "element": {"foo": "bar"},
                "A": 1,
                "B": [2, 3, 4, 5, 6],
                "dependencies": ["numpy"],
                "marker": {"name": "fc"},
                "type": "BOLD",
            },
            ["foo"],
        ),
        (
            {
                "element": {"subject": "foo", "session": "bar"},
                "B": [2, 3, 4, 5, 6],
                "A": 1,
                "dependencies": ["numpy"],
                "marker": {"name": "fc"},
                "type": "BOLD",
            },
            ["subject", "session"],
        ),
    ],
)
def test_process_meta_element(meta: dict, elements: list[str]) -> None:
    """Test metadata element after processing.

    Parameters
    ----------
    meta : dict
        The parametrized metadata dictionary.
    elements : list of str
        The parametrized elements to assert against.

    """
    hash1, processed_meta, _ = process_meta(meta)
    assert "_element_keys" in processed_meta
    assert processed_meta["_element_keys"] == elements
    assert "A" in processed_meta
    assert "B" in processed_meta
    assert "element" not in processed_meta
    assert isinstance(processed_meta["dependencies"], dict)
    assert all(
        x in processed_meta["dependencies"] for x in meta["dependencies"]
    )
    assert "name" in processed_meta
    assert processed_meta["name"] == f"{meta['type']}_{meta['marker']['name']}"


@pytest.mark.parametrize(
    "element,prefix",
    [
        ({"subject": "sub-01"}, "element_sub-01_"),
        ({"subject": 1}, "element_1_"),
        ({"subject": "sub-01", "session": "ses-02"}, "element_sub-01_ses-02_"),
        ({"subject": 1, "session": 2}, "element_1_2_"),
    ],
)
def test_element_to_prefix(element: dict, prefix: str) -> None:
    """Test converting element to prefix (for file naming).

    Parameters
    ----------
    element : str, int, dict or tuple
        The parameterized element.
    prefix : str
        The parametrized prefix to assert against.

    """
    prefix_generated = element_to_prefix(element)
    assert prefix_generated == prefix


def test_element_to_prefix_invalid_type() -> None:
    """Test element to prefix type checking."""
    element = 2.3
    with pytest.raises(ValueError, match=r"must be a dict"):
        element_to_prefix(element)  # type: ignore


@pytest.mark.parametrize(
    "params, err_msg",
    [
        (
            {
                "matrix_kind": "half",
                "diagonal": True,
                "data_shape": (1, 1),
                "row_names_len": 1,
                "col_names_len": 1,
            },
            "Invalid kind",
        ),
        (
            {
                "matrix_kind": "full",
                "diagonal": False,
                "data_shape": (1, 1),
                "row_names_len": 1,
                "col_names_len": 1,
            },
            "Diagonal cannot",
        ),
        (
            {
                "matrix_kind": "triu",
                "diagonal": False,
                "data_shape": (2, 1),
                "row_names_len": 2,
                "col_names_len": 1,
            },
            "Cannot store a non-square",
        ),
        (
            {
                "matrix_kind": "tril",
                "diagonal": False,
                "data_shape": (1, 2),
                "row_names_len": 1,
                "col_names_len": 2,
            },
            "Cannot store a non-square",
        ),
        (
            {
                "matrix_kind": "full",
                "diagonal": True,
                "data_shape": (2, 2),
                "row_names_len": 1,
                "col_names_len": 2,
            },
            "Number of row names",
        ),
        (
            {
                "matrix_kind": "full",
                "diagonal": True,
                "data_shape": (2, 2),
                "row_names_len": 2,
                "col_names_len": 1,
            },
            "Number of column names",
        ),
    ],
)
def test_store_matrix_checks(
    params: dict[str, Union[str, bool, tuple[int, int], int]], err_msg: str
) -> None:
    """Test matrix storing parameter checks.

    Parameters
    ----------
    params : dict
        The parametrized parameters for the function.
    err_msg : str
        The parametrized substring of expected error message.

    """
    with pytest.raises(ValueError, match=f"{err_msg}"):
        store_matrix_checks(**params)  # type: ignore


@pytest.mark.parametrize(
    "params, expected_data, expected_columns",
    [
        (
            {
                "data": np.arange(9).reshape(3, 3),
                "col_names": ["c0", "c1", "c2"],
                "row_names": ("r0", "r1", "r2"),
                "matrix_kind": "triu",
                "diagonal": True,
            },
            np.array([0, 1, 2, 4, 5, 8]),
            ["r0~c0", "r0~c1", "r0~c2", "r1~c1", "r1~c2", "r2~c2"],
        ),
        (
            {
                "data": np.arange(9).reshape(3, 3),
                "col_names": ("c0", "c1", "c2"),
                "row_names": ["r0", "r1", "r2"],
                "matrix_kind": "triu",
                "diagonal": False,
            },
            np.array([1, 2, 5]),
            ["r0~c1", "r0~c2", "r1~c2"],
        ),
        (
            {
                "data": np.arange(9).reshape(3, 3),
                "col_names": ("c0", "c1", "c2"),
                "row_names": ["r0", "r1", "r2"],
                "matrix_kind": "tril",
                "diagonal": True,
            },
            np.array([0, 3, 4, 6, 7, 8]),
            ["r0~c0", "r1~c0", "r1~c1", "r2~c0", "r2~c1", "r2~c2"],
        ),
        (
            {
                "data": np.arange(9).reshape(3, 3),
                "col_names": ("c0", "c1", "c2"),
                "row_names": ["r0", "r1", "r2"],
                "matrix_kind": "tril",
                "diagonal": False,
            },
            np.array([3, 6, 7]),
            ["r1~c0", "r2~c0", "r2~c1"],
        ),
        (
            {
                "data": np.arange(9).reshape(3, 3),
                "col_names": ("c0", "c1", "c2"),
                "row_names": ["r0", "r1", "r2"],
                "matrix_kind": "full",
                "diagonal": False,
            },
            np.arange(9),
            [
                f"{r}~{c}"
                for r in ["r0", "r1", "r2"]
                for c in ["c0", "c1", "c2"]
            ],
        ),
    ],
)
def test_matrix_to_vector(
    params: dict[str, Union[np.ndarray, Iterable[str], str, bool]],
    expected_data: np.ndarray,
    expected_columns: list[str],
) -> None:
    """Test matrix to vector.

    Parameters
    ----------
    params : dict
        The parametrized parameters for the function.
    expected_data : np.ndarray
        The parametrized vector data to expect.
    expected_columns : np.ndarray
        The parametrized columns labels to expect.

    """
    data, columns = matrix_to_vector(**params)  # type: ignore
    assert_array_equal(data, expected_data)
    assert columns == expected_columns


def test_timeseries2d_to_vector() -> None:
    """Test timeseries2d to vector."""
    data = np.array(
        [[10, 11, 12], [20, 21, 22], [30, 31, 32], [40, 41, 42], [50, 51, 52]]
    )
    data = np.c_[[data + (i * 100) for i in range(4)]]  # Generate timeseries
    col_names = ["c0", "c1", "c2"]
    row_names = ["r0", "r1", "r2", "r3", "r4"]
    flat_data, columns = timeseries2d_to_vector(
        data=data,
        col_names=col_names,
        row_names=row_names,
    )

    expected_flat_data = np.array(
        [10, 11, 12, 20, 21, 22, 30, 31, 32, 40, 41, 42, 50, 51, 52]
    )
    expected_flat_data = np.c_[
        [expected_flat_data + (i * 100) for i in range(4)]
    ]  # Generate timeseries
    assert_array_equal(flat_data, expected_flat_data)
    assert columns == [f"{r}~{c}" for r in row_names for c in col_names]
