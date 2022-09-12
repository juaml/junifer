"""Provide tests for utils."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Dict, List, Tuple, Union

import pytest

from junifer.storage.utils import (
    element_to_index,
    element_to_prefix,
    process_meta,
)


def test_process_meta_invalid_metadata_type() -> None:
    """Test invalid metadata type check for metadata hash processing."""
    meta = None
    with pytest.raises(ValueError, match=r"`meta` must be a dict"):
        process_meta(meta)  # type: ignore


# TODO: parameterize
def test_process_meta_hash() -> None:
    """Test metadata hash processing."""
    meta = {"element": "foo", "A": 1, "B": [2, 3, 4, 5, 6]}
    hash1, _ = process_meta(meta)

    meta = {"element": "foo", "B": [2, 3, 4, 5, 6], "A": 1}
    hash2, _ = process_meta(meta)
    assert hash1 == hash2

    meta = {"element": "foo", "A": 1, "B": [2, 3, 1, 5, 6]}
    hash3, _ = process_meta(meta)
    assert hash1 != hash3

    meta1 = {
        "element": "foo",
        "B": {
            "B2": [2, 3, 4, 5, 6],
            "B1": [9.22, 3.14, 1.41, 5.67, 6.28],
            "B3": (1, "car"),
        },
        "A": 1,
    }

    meta2 = {
        "A": 1,
        "B": {
            "B3": (1, "car"),
            "B1": [9.22, 3.14, 1.41, 5.67, 6.28],
            "B2": [2, 3, 4, 5, 6],
        },
        "element": "foo",
    }

    hash4, _ = process_meta(meta1)
    hash5, _ = process_meta(meta2)
    assert hash4 == hash5


def test_process_meta_invalid_metadata_key() -> None:
    """Test invalid metadata key check for metadata hash processing."""
    meta = {}
    with pytest.raises(ValueError, match=r"_element_keys"):
        process_meta(meta)


@pytest.mark.parametrize(
    "meta,elements",
    [
        ({"element": "foo", "A": 1, "B": [2, 3, 4, 5, 6]}, ["element"]),
        (
            {
                "element": {"subject": "foo", "session": "bar"},
                "B": [2, 3, 4, 5, 6],
                "A": 1,
            },
            ["subject", "session"],
        ),
    ],
)
def test_process_meta_element(meta: Dict, elements: List[str]) -> None:
    """Test metadata element after processing.

    Parameters
    ----------
    meta : dict
        The parametrized metadata dictionary.
    elements : list of str
        The parametrized elements to assert against.

    """
    _, processed_meta = process_meta(meta)
    assert "_element_keys" in processed_meta
    assert processed_meta["_element_keys"] == elements
    assert "A" in processed_meta
    assert "B" in processed_meta


@pytest.mark.parametrize(
    "element,prefix",
    [
        ("sub-01", "element_sub-01_"),
        (1, "element_1_"),
        ({"subject": "sub-01"}, "element_sub-01_"),
        ({"subject": 1}, "element_1_"),
        ({"subject": "sub-01", "session": "ses-02"}, "element_sub-01_ses-02_"),
        ({"subject": 1, "session": 2}, "element_1_2_"),
        (("sub-01", "ses-02"), "element_sub-01_ses-02_"),
        ((1, 2), "element_1_2_"),
    ],
)
def test_element_to_prefix(
    element: Union[str, int, Dict, Tuple], prefix: str
) -> None:
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


def test_element_to_index_check_meta_invalid_key() -> None:
    """Test element to index metadata key checking."""
    meta = {"noelement": "foo"}
    with pytest.raises(ValueError, match=r"metadata must contain the key"):
        element_to_index(meta)


def test_element_to_index() -> None:
    """Test element to index."""
    meta = {"element": "foo", "A": 1, "B": [2, 3, 4, 5, 6]}
    index = element_to_index(meta)
    assert index.names == ["element", "idx"]
    assert index.levels[0].name == "element"
    assert index.levels[0].values[0] == "foo"
    assert all(x == "foo" for x in index.levels[0].values)
    assert index.levels[0].values.shape == (1,)
    assert index.levels[1].name == "idx"
    assert all(x == i for i, x in enumerate(index.levels[1].values))
    assert index.levels[1].values.shape == (1,)

    index = element_to_index(meta, n_rows=10)
    assert index.names == ["element", "idx"]
    assert index.levels[0].name == "element"
    assert all(x == "foo" for x in index.levels[0].values)
    assert index.levels[0].values.shape == (1,)

    assert index.levels[1].name == "idx"
    assert all(x == i for i, x in enumerate(index.levels[1].values))
    assert index.levels[1].values.shape == (10,)

    index = element_to_index(meta, n_rows=1, rows_col_name="scan")
    assert index.names == ["element", "scan"]
    assert index.levels[0].name == "element"
    assert index.levels[0].values[0] == "foo"
    assert all(x == "foo" for x in index.levels[0].values)
    assert index.levels[0].values.shape == (1,)
    assert index.levels[1].name == "scan"
    assert all(x == i for i, x in enumerate(index.levels[1].values))
    assert index.levels[1].values.shape == (1,)

    index = element_to_index(meta, n_rows=7, rows_col_name="scan")
    assert index.names == ["element", "scan"]
    assert index.levels[0].name == "element"
    assert all(x == "foo" for x in index.levels[0].values)
    assert index.levels[0].values.shape == (1,)

    assert index.levels[1].name == "scan"
    assert all(x == i for i, x in enumerate(index.levels[1].values))
    assert index.levels[1].values.shape == (7,)

    meta = {
        "element": {"subject": "sub-01", "session": "ses-01"},
        "A": 1,
        "B": [2, 3, 4, 5, 6],
    }
    index = element_to_index(meta, n_rows=10)

    assert index.levels[0].name == "subject"
    assert all(x == "sub-01" for x in index.levels[0].values)
    assert index.levels[0].values.shape == (1,)

    assert index.levels[1].name == "session"
    assert all(x == "ses-01" for x in index.levels[1].values)
    assert index.levels[1].values.shape == (1,)

    assert index.levels[2].name == "idx"
    assert all(x == i for i, x in enumerate(index.levels[2].values))
    assert index.levels[2].values.shape == (10,)
