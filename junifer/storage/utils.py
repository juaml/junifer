"""Provide utility functions for the storage sub-package."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import hashlib
import json
from collections.abc import Iterable
from importlib.metadata import PackageNotFoundError, version

import numpy as np

from ..utils.logging import logger, raise_error


__all__ = [
    "element_to_prefix",
    "get_dependency_version",
    "matrix_to_vector",
    "process_meta",
    "store_matrix_checks",
]


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


def _meta_hash(meta: dict) -> str:
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


def process_meta(meta: dict) -> tuple[str, dict, dict]:
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
    element: dict = t_meta.pop("element", None)
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


def element_to_prefix(element: dict) -> str:
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
    data_shape: tuple[int, int],
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

    Raises
    ------
    ValueError
        If the matrix kind is invalid
        If the diagonal is False and the matrix kind is "full"
        If the matrix kind is "triu" or "tril" and the matrix is not square
        If the number of row names does not match the number of rows
        If the number of column names does not match the number of columns

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


def store_timeseries_2d_checks(
    data_shape: tuple[int, int, int],
    row_names_len: int,
    col_names_len: int,
) -> None:
    """Run parameter checks for store_timeseries_2d() methods.

    Parameters
    ----------
    data_shape : tuple of int and int
        The shape of the matrix data to store.
    row_names_len : int
        The length of row labels.
    col_names_len : int
        The length of column labels.

    Raises
    ------
    ValueError
        If the data is not a 3D array (timepoints, rows, columns)
        If the number of row names does not match the number of rows
        If the number of column names does not match the number of columns

    """
    # data validation
    if len(data_shape) != 3:
        raise_error(
            msg="Data must be a 3D array",
            klass=ValueError,
        )

    # Row label validation
    if row_names_len != data_shape[1]:  # type: ignore
        raise_error(
            msg="Number of row names does not match number of rows",
            klass=ValueError,
        )
    # Column label validation
    if col_names_len != data_shape[2]:  # type: ignore
        raise_error(
            msg="Number of column names does not match number of columns",
            klass=ValueError,
        )


def matrix_to_vector(
    data: np.ndarray,
    col_names: Iterable[str],
    row_names: Iterable[str],
    matrix_kind: str,
    diagonal: bool,
) -> tuple[np.ndarray, list[str]]:
    """Convert matrix to vector based on parameters.

    Parameters
    ----------
    data : 2D / 3D numpy.ndarray
        The matrix / tensor data to store / read.
    col_names : list or tuple of str
        The column labels.
    row_names : list or tuple of str
        The row labels.
    matrix_kind : str
        The kind of matrix:

        * ``triu`` : store upper triangular only
        * ``tril`` : store lower triangular
        * ``full`` : full matrix

    diagonal : bool
        Whether to store the diagonal.

    Returns
    -------
    1D / 2D numpy.ndarray
        The vector / matrix data.
    list of str
        The column labels.

    """
    # Prepare data indexing based on matrix kind
    if matrix_kind == "triu":
        k = 0 if diagonal is True else 1
        data_idx = np.triu_indices(data.shape[0], k=k)
    elif matrix_kind == "tril":
        k = 0 if diagonal is True else -1
        data_idx = np.tril_indices(data.shape[0], k=k)
    else:  # full
        data_idx = (
            np.repeat(np.arange(data.shape[0]), data.shape[1]),
            np.tile(np.arange(data.shape[1]), data.shape[0]),
        )
    # Subset data as 1D
    flat_data = data[data_idx]
    # Generate flat 1D row X column names
    columns = [
        f"{row_names[i]}~{col_names[j]}"  # type: ignore
        for i, j in zip(data_idx[0], data_idx[1])
    ]

    return flat_data, columns


def timeseries2d_to_vector(
    data: np.ndarray,
    col_names: Iterable[str],
    row_names: Iterable[str],
) -> tuple[np.ndarray, list[str]]:
    """Convert matrix to vector based on parameters.

    Parameters
    ----------
    data : 2D / 3D numpy.ndarray
        The matrix / tensor data to store / read.
    col_names : list or tuple of str
        The column labels.
    row_names : list or tuple of str
        The row labels.

    Returns
    -------
    2D numpy.ndarray
        The vector / matrix data.
    list of str
        The column labels.

    """
    # Reshape data to 2D
    flat_data = data.reshape(data.shape[0], -1)
    # Generate flat 1D row X column names
    columns = [f"{r}~{c}" for r in row_names for c in col_names]

    return flat_data, columns
