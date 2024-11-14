"""Provide abstract base class for feature storage via pandas."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Optional, Union

import numpy as np
import pandas as pd

from ..utils import raise_error
from .base import BaseFeatureStorage


__all__ = ["PandasBaseFeatureStorage"]


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

    def get_valid_inputs(self) -> list[str]:
        """Get valid storage types for input.

        Returns
        -------
        list of str
            The list of storage types that can be used as input for this
            storage interface.

        """
        return ["matrix", "vector", "timeseries"]

    def _meta_row(self, meta: dict, meta_md5: str) -> pd.DataFrame:
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
        element: dict, n_rows: int = 1, rows_col_name: Optional[str] = None
    ) -> Union[pd.Index, pd.MultiIndex]:
        """Convert the element metadata to index.

        Parameters
        ----------
        element : dict
            The element as a dictionary.
        n_rows : int, optional
            Number of rows to create (default 1).
        rows_col_name: str, optional
            The column name to use in case ``n_rows`` > 1. If None and
            ``n_rows`` > 1, the name will be "idx" (default None).

        Returns
        -------
        pandas.Index or pandas.MultiIndex
            The index of the dataframe to store.

        """
        # Make mapping between element access keys and values
        elem_idx: dict[str, Iterable[str]] = {
            k: [v] * n_rows for k, v in element.items()
        }

        # Set rows_col_name if n_rows > 1 (timeseries)
        if n_rows > 1:
            # Set rows_col_name if None
            if rows_col_name is None:
                rows_col_name = "idx"
            # Set extra column for variable number of rows per element
            elem_idx[rows_col_name] = np.arange(n_rows)

        # Create correct index for elements with single access variable
        if len(elem_idx) == 1:
            # Create normal index for vector
            index = pd.Index(
                data=next(iter(elem_idx.values())),
                name=next(iter(elem_idx.keys())),
            )
        else:
            # Create multiindex for timeseries
            index = pd.MultiIndex.from_frame(
                pd.DataFrame(elem_idx, index=range(n_rows))
            )

        return index

    def store_df(
        self, meta_md5: str, element: dict, df: Union[pd.DataFrame, pd.Series]
    ) -> None:
        """Implement pandas DataFrame storing.

        Parameters
        ----------
        meta_md5 : str
            The metadata MD5 hash.
        element : dict
            The element as a dictionary.
        df : pandas.DataFrame or pandas.Series
            The pandas DataFrame or Series to store.

        Raises
        ------
        ValueError
            If the dataframe index has items that are not in the index
            generated from the metadata.

        """
        raise_error(
            msg="Concrete classes need to implement store_df().",
            klass=NotImplementedError,
        )

    def _store_2d(
        self,
        meta_md5: str,
        element: dict,
        data: Union[np.ndarray, list],
        col_names: Optional[Iterable[str]] = None,
        rows_col_name: Optional[str] = None,
    ) -> None:
        """Store 2D data.

        Parameters
        ----------
        meta_md5 : str
            The metadata MD5 hash.
        element : dict
            The element as a dictionary.
        data : numpy.ndarray or list
            The data to store.
        col_names : list or tuple of str, optional
            The column labels (default None).
        rows_col_name : str, optional
            The column name to use in case number of rows greater than 1.
            If None and number of rows greater than 1, then the name will be
            "idx" (default None).

        """
        # Convert element metadata to index
        idx = self.element_to_index(
            element=element, n_rows=len(data), rows_col_name=rows_col_name
        )
        # Prepare new dataframe
        df = pd.DataFrame(
            data=data, columns=col_names, index=idx  # type: ignore
        )
        # Store dataframe
        self.store_df(meta_md5=meta_md5, element=element, df=df)

    def store_vector(
        self,
        meta_md5: str,
        element: dict,
        data: Union[np.ndarray, list],
        col_names: Optional[Iterable[str]] = None,
    ) -> None:
        """Store vector.

        Parameters
        ----------
        meta_md5 : str
            The metadata MD5 hash.
        element : dict
            The element as a dictionary.
        data : numpy.ndarray or list
            The vector data to store.
        col_names : list or tuple of str, optional
            The column labels (default None).

        """
        if isinstance(data, list):
            # Flatten out list and convert to np.ndarray
            processed_data = np.array(np.ravel(data))
        elif isinstance(data, np.ndarray):
            # Flatten out array
            processed_data = data.ravel()

        # Make it 2D
        processed_data = processed_data[np.newaxis, :]

        self._store_2d(
            meta_md5=meta_md5,
            element=element,
            data=data,
            col_names=col_names,
        )

    def store_timeseries(
        self,
        meta_md5: str,
        element: dict,
        data: np.ndarray,
        col_names: Optional[Iterable[str]] = None,
    ) -> None:
        """Store timeseries.

        Parameters
        ----------
        meta_md5 : str
            The metadata MD5 hash.
        element : dict
            The element as a dictionary.
        data : numpy.ndarray
            The timeseries data to store.
        col_names : list or tuple of str, optional
            The column labels (default None).

        """
        self._store_2d(
            meta_md5=meta_md5,
            element=element,
            data=data,
            col_names=col_names,
            rows_col_name="timepoint",
        )
