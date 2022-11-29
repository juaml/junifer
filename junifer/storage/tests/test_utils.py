"""Provide tests for utils."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Dict, List

import pytest

from junifer.storage.utils import (
    element_to_prefix,
    get_dependency_version,
    process_meta,
)


@pytest.mark.parametrize(
    "dependency, max_version",
    [
        ("click", "8.2"),
        ("numpy", "1.24"),
        ("datalad", "0.18"),
        ("pandas", "1.6"),
        ("nibabel", "4.1"),
        ("nilearn", "1.0"),
        ("sqlalchemy", "1.5.0"),
        ("pyyaml", "7.0"),
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
def test_process_meta_element(meta: Dict, elements: List[str]) -> None:
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
    assert isinstance(processed_meta["dependencies"], Dict)
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
def test_element_to_prefix(element: Dict, prefix: str) -> None:
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
