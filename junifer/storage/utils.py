"""Provide utility functions for the storage sub-package."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import hashlib
import json
from importlib.metadata import PackageNotFoundError, version
from typing import Dict, Tuple

from ..utils.logging import logger, raise_error


def get_dependency_version(dependency: str) -> str:
    """Get dependency version.

    Parameters
    ----------
    dependency : str
         The dependency to fetch version for.

    Returns
    -------
    str
        The version of the dependency.

    """
    dep_version = ""
    try:
        dep_version = version(dependency)
    except PackageNotFoundError as e:
        raise_error(
            f"Could not obtain the version of {dependency}. "
            "Have you specified the DEPENDENCIES variable correctly?",
            exception=e,
        )

    return dep_version


def _meta_hash(meta: Dict) -> str:
    """Compute the MD5 hash of the metadata.

    Parameters
    ----------
    meta : dict
        The metadata as a dictionary. Must contain the key "element".

    Returns
    -------
    str
        The MD5 hash of the metadata.

    """
    logger.debug(f"Hashing metadata: {meta}")
    if "dependencies" not in meta:
        raise_error("The metadata must contain the key 'dependencies'")
    # Convert dependencies set into {dependency: version} dictionary
    meta["dependencies"] = {
        dep: get_dependency_version(dep) for dep in meta["dependencies"]
    }
    meta_md5 = hashlib.md5(
        json.dumps(meta, sort_keys=True).encode("utf-8")
    ).hexdigest()
    logger.debug(f"Hash computed: {meta_md5}")
    return meta_md5


def process_meta(meta: Dict) -> Tuple[str, Dict, Dict]:
    """Process the metadata for storage.

    It removes the key "element" and adds the "_element_keys" with the keys
    used to index the element.

    Parameters
    ----------
    meta : dict
        The metadata as a dictionary. Must contain the key "element".

    Returns
    -------
    str
        The MD5 hash of the metadata.
    dict
        The processed metadata for storage.
    dict
        The element.

    Raises
    ------
    ValueError
        If ``meta`` is None or if it does not contain the key "element".

    """
    if meta is None:
        raise_error(msg="`meta` must be a dict (currently is None)")
    # Copy the metadata
    t_meta = meta.copy()
    # Remove key "element"
    element: Dict = t_meta.pop("element", None)
    if element is None:
        raise_error(msg="`meta` must contain the key 'element'")
    if "marker" not in t_meta:
        raise_error(msg="`meta` must contain the key 'marker'")
    if "name" not in t_meta["marker"]:
        raise_error(msg="`meta['marker']` must contain the key 'name'")
    if "type" not in t_meta:
        raise_error(msg="`meta` must contain the key 'type'")

    t_meta["_element_keys"] = list(element.keys())
    type_ = t_meta["type"]
    name = t_meta["marker"]["name"]
    t_meta["name"] = f"{type_}_{name}"
    # MD5 hash of the metadata
    md5_hash = _meta_hash(t_meta)
    return md5_hash, t_meta, element


def element_to_prefix(element: Dict) -> str:
    """Convert the element metadata to prefix.

    Parameters
    ----------
    element : dict
        The element to convert to prefix.

    Returns
    -------
    str
        The element converted to prefix.
    """
    logger.debug(f"Converting element {element} to prefix.")
    prefix = "element"
    if not isinstance(element, dict):
        raise_error(msg="`element` must be a dict")

    prefix = f"{prefix}_{'_'.join([f'{x}' for x in element.values()])}"

    logger.debug(f"Converted prefix: {prefix}")
    return f"{prefix}_"


def store_matrix_checks(
    matrix_kind: str,
    diagonal: bool,
    data_shape: Tuple[int, int],
    row_names_len: int,
    col_names_len: int,
) -> None:
    """Run parameter checks for store_matrix() methods.

    Parameters
    ----------
    matrix_kind : {"triu", "tril", "full"}
        The kind of matrix:

        * ``triu`` : store upper triangular only
        * ``tril`` : store lower triangular
        * ``full`` : full matrix

    diagonal : bool
        Whether to store the diagonal. If ``matrix_kind`` is "full",
        setting this to False will raise an error.
    data_shape : tuple of int and int
        The shape of the matrix data to store.
    row_names_len : int
        The length of row labels.
    col_names_len : int
        The length of column labels.

    """
    # Matrix kind validation
    if matrix_kind not in ("triu", "tril", "full"):
        raise_error(msg=f"Invalid kind {matrix_kind}", klass=ValueError)
    # Diagonal validation
    if diagonal is False and matrix_kind not in ["triu", "tril"]:
        raise_error(
            msg="Diagonal cannot be False if kind is not full",
            klass=ValueError,
        )
    # Matrix kind and shape validation
    if matrix_kind in ["triu", "tril"]:
        if data_shape[0] != data_shape[1]:
            raise_error(
                "Cannot store a non-square matrix as a triangular matrix",
                klass=ValueError,
            )
    # Row label validation
    if row_names_len != data_shape[0]:  # type: ignore
        raise_error(
            msg="Number of row names does not match number of rows",
            klass=ValueError,
        )
    # Column label validation
    if col_names_len != data_shape[1]:  # type: ignore
        raise_error(
            msg="Number of column names does not match number of columns",
            klass=ValueError,
        )
