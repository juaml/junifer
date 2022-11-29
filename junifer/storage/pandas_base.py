"""Provide abstract base class for feature storage via pandas."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union

import numpy as np
import pandas as pd

from .base import BaseFeatureStorage


class PandasBaseFeatureStorage(BaseFeatureStorage):
    """Abstract base class for feature storage via pandas.

    For every interface that is required, one needs to provide a concrete
    implementation of this abstract class.

    Parameters
    ----------
    uri : str or pathlib.Path
        The path to the storage.
    single_output : bool, optional
        Whether to have single output (default True).
    **kwargs
        Keyword arguments passed to superclass.

    See Also
    --------
    BaseFeatureStorage : The base class for feature storage.

    """

    def __init__(
        self, uri: Union[str, Path], single_output: bool = True, **kwargs
    ) -> None:
        super().__init__(uri=uri, single_output=single_output, **kwargs)

    def get_valid_inputs(self) -> List[str]:
        """Get valid storage types for input.

        Returns
        -------
        list of str
            The list of storage types that can be used as input for this "
            "storage.
        """
        return ["matrix", "table", "timeseries"]

    def _meta_row(self, meta: Dict, meta_md5: str) -> pd.DataFrame:
        """Convert the metadata to a pandas DataFrame.

        Parameters
        ----------
        meta : dict
            The metadata as a dictionary.
        meta_md5 : str
            The MD5 hash of the metadata.

        Returns
        -------
        pandas.DataFrame

        """
        data_df = {}
        for k, v in meta.items():
            data_df[k] = json.dumps(v, sort_keys=True)
        df = pd.DataFrame(data_df, index=[meta_md5])
        df.index.name = "meta_md5"
        return df

    @staticmethod
    def element_to_index(
        element: Dict, n_rows: int = 1, rows_col_name: Optional[str] = None
    ) -> pd.MultiIndex:
        """Convert the element metadata to index.

        Parameters
        ----------
        element : dict
            The element as a dictionary.
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
        # Check rows_col_name
        if rows_col_name is None:
            rows_col_name = "idx"
        elem_idx: Dict[Any, Any] = {
            k: [v] * n_rows for k, v in element.items()
        }
        elem_idx[rows_col_name] = np.arange(n_rows)
        # Create index
        index = pd.MultiIndex.from_frame(
            pd.DataFrame(elem_idx, index=range(n_rows))
        )
        return index

    def store_df(
        self, meta_md5: str, element: Dict, df: Union[pd.DataFrame, pd.Series]
    ) -> None:
        """Implement pandas DataFrame storing.

        Parameters
        ----------
        df : pandas.DataFrame or pandas.Series
            The pandas DataFrame or Series to store.
        meta : dict
            The metadata as a dictionary.

        Raises
        ------
        ValueError
            If the dataframe index has items that are not in the index
            generated from the metadata.

        """
        raise NotImplementedError("Implement in subclass.")

    def _store_2d(
        self,
        meta_md5: str,
        element: Dict,
        data: Union[np.ndarray, List],
        columns: Optional[Iterable[str]] = None,
        rows_col_name: Optional[str] = None,
    ) -> None:
        """Store 2D dataframe.

        Parameters
        ----------
        meta_md5 : str
            The metadata MD5 hash.
        element : dict
            The element as a dictionary.
        data : numpy.ndarray or List
            The data to store.
        columns : list or tuple of str, optional
            The columns (default None).
        rows_col_name : str, optional
            The column name to use in case number of rows greater than 1.
            If None and number of rows greater than 1, then the name will be
            "index" (default None).

        """
        n_rows = len(data)
        # Convert element metadata to index
        idx = self.element_to_index(
            element=element, n_rows=n_rows, rows_col_name=rows_col_name
        )
        # Prepare new dataframe
        data_df = pd.DataFrame(  # type: ignore
            data, columns=columns, index=idx  # type: ignore
        )
        # Store dataframe
        self.store_df(meta_md5=meta_md5, element=element, df=data_df)

    def store_table(
        self,
        meta_md5: str,
        element: Dict,
        data: Union[np.ndarray, List],
        columns: Optional[Iterable[str]] = None,
        rows_col_name: Optional[str] = None,
    ) -> None:
        """Implement table storing.

        Parameters
        ----------
        meta_md5 : str
            The metadata MD5 hash.
        element : dict
            The element as a dictionary.
        data : numpy.ndarray or List
            The table data to store.
        columns : list or tuple of str, optional
            The columns (default None).
        rows_col_name : str, optional
            The column name to use in case number of rows greater than 1.
            If None and number of rows greater than 1, then the name will be
            "index" (default None).
        """
        self._store_2d(
            meta_md5=meta_md5,
            element=element,
            data=data,
            columns=columns,
            rows_col_name=rows_col_name,
        )

    def store_timeseries(
        self,
        meta_md5: str,
        element: Dict,
        data: np.ndarray,
        columns: Optional[Iterable[str]] = None,
    ) -> None:
        """Implement timeseries storing.

        Parameters
        ----------
        meta_md5 : str
            The metadata MD5 hash.
        element : dict
            The element as a dictionary.
        data : numpy.ndarray
            The timeseries data to store.
        columns : list or tuple of str, optional
            The column labels (default None).
        """
        self._store_2d(
            meta_md5=meta_md5,
            element=element,
            data=data,
            columns=columns,
            rows_col_name="timepoint",
        )
