"""Provide utility functions for the storage sub-package."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import hashlib
import json
from typing import Any, Dict, Optional, Tuple, Union

import numpy as np
import pandas as pd

from ..utils.logging import logger, raise_error


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
    meta_md5 = hashlib.md5(
        json.dumps(meta, sort_keys=True).encode("utf-8")
    ).hexdigest()
    logger.debug(f"Hash computed: {meta_md5}")
    return meta_md5


def process_meta(meta: Dict) -> Tuple[str, Dict]:
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

    Raises
    ------
    ValueError
        If `meta` is None or if it does not contain the key "element" or
        "_element_keys".

    """
    if meta is None:
        raise_error(msg="`meta` must be a dict (currently is None)")
    # Copy the metadata
    t_meta = meta.copy()
    # Remove key "element"
    element = t_meta.pop("element", None)
    if element is None:
        if "_element_keys" not in t_meta:
            raise_error(
                msg="`meta` must contain the key 'element' or '_element_keys'"
            )
    else:
        if isinstance(element, dict):
            t_meta["_element_keys"] = list(element.keys())
        else:
            t_meta["_element_keys"] = ["element"]
    # MD5 hash of the metadata
    md5_hash = _meta_hash(t_meta)
    return md5_hash, t_meta


def element_to_prefix(element: Union[Tuple, Dict, str, int]) -> str:
    """Convert the element metadata to prefix.

    Parameters
    ----------
    element : tuple, dict, str or int
        The element to convert to prefix.

    Returns
    -------
    str
        The element converted to prefix.

    Raises
    ------
    ValueError
        If invalid type is passed for `element`.

    """
    logger.debug(f"Converting element {element} to prefix.")
    prefix = "element"
    if isinstance(element, tuple):
        prefix = f"{prefix}_{'_'.join([f'{x}' for x in element])}"
    elif isinstance(element, dict):
        prefix = f"{prefix}_{'_'.join([f'{x}' for x in element.values()])}"
    elif isinstance(element, (str, int)):
        prefix = f"{prefix}_{element}"
    else:
        raise_error(
            f"Cannot convert element of type {type(element)} to prefix. "
            "Must be a str, int, tuple or dict."
        )
    logger.debug(f"Converted prefix: {prefix}")
    return f"{prefix}_"


def element_to_index(
    meta: Dict, n_rows: int = 1, rows_col_name: Optional[str] = None
) -> pd.MultiIndex:
    """Convert the element metadata to index.

    Parameters
    ----------
    meta : dict
        The metadata as a dictionary. Must contain the key "element"."
    n_rows : int, optional
        Number of rows to create (default 1).
    rows_col_name: str, optional
        The column name to use in case `n_rows` > 1. If None and
        n_rows > 1, the name will be "idx" (default None).

    Returns
    -------
    pandas.MultiIndex
        The index of the dataframe to store.

    Raises
    ------
    ValueError
        If `meta` does not contain the key "element".

    """
    if "element" not in meta:
        raise_error(
            msg="To create and index, metadata must contain the key 'element'."
        )
    # Get element
    element = meta["element"]
    if not isinstance(element, dict):
        element = {"element": element}
    # Check rows_col_name
    if rows_col_name is None:
        rows_col_name = "idx"
    elem_idx: Dict[Any, Any] = {k: [v] * n_rows for k, v in element.items()}
    elem_idx[rows_col_name] = np.arange(n_rows)
    # Create index
    index = pd.MultiIndex.from_frame(
        pd.DataFrame(elem_idx, index=range(n_rows))
    )
    return index
