"""Provide abstract base class for feature storage."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Union

import numpy as np
import pandas as pd

from ..utils import raise_error
from .utils import process_meta


class BaseFeatureStorage(ABC):
    """Abstract base class for feature storage.

    For every interface that is required, one needs to provide a concrete
    implementation of this abstract class.

    Parameters
    ----------
    uri : str or pathlib.Path
        The path to the storage.
    storage_types : str or list of str
        The available storage types for the class.
    single_output : bool, optional
        Whether to have single output (default True).

    """

    def __init__(
        self,
        uri: Union[str, Path],
        storage_types: Union[List[str], str],
        single_output: bool = True,
    ) -> None:
        self.uri = uri
        if not isinstance(storage_types, list):
            storage_types = [storage_types]
        if any(x not in self.get_valid_inputs() for x in storage_types):
            wrong_storage_types = [
                x for x in storage_types if x not in self.get_valid_inputs()
            ]
            raise ValueError(
                f"{self.__class__.__name__} cannot store {wrong_storage_types}"
            )
        self._valid_inputs = storage_types
        self.single_output = single_output

    def get_valid_inputs(self) -> List[str]:
        """Get valid storage types for input.

        Returns
        -------
        list of str
            The list of storage types that can be used as input for this "
            "storage.
        """
        raise_error(
            msg="Concrete classes need to implement get_valid_inputs().",
            klass=NotImplementedError,
        )

    def validate(self, input_: List[str]) -> None:
        """Validate the input to the pipeline step.

        Parameters
        ----------
        input_ : list of str
            The input to the pipeline step.

        Raises
        ------
        ValueError
            If the ``input_`` is invalid.

        """
        if not any(x in input_ for x in self._valid_inputs):
            raise_error(
                "Input does not have the required data."
                f"\t Input: {input}"
                f"\t Required (any of): {self._valid_inputs}"
            )

    @abstractmethod
    def list_features(self) -> Dict:
        """List the features in the storage.

        Returns
        -------
        dict
            List of features in the storage. The keys are the feature names to
            be used in read_features() and the values are the metadata of each
            feature.

        """
        raise_error(
            msg="Concrete classes need to implement list_features().",
            klass=NotImplementedError,
        )

    @abstractmethod
    def read_df(
        self,
        feature_name: Optional[str] = None,
        feature_md5: Optional[bool] = None,
    ) -> pd.DataFrame:
        """Read feature into a pandas DataFrame.

        Parameters
        ----------
        feature_name : str, optional
            Name of the feature to read (default None).
        feature_md5 : str, optional
            MD5 hash of the feature to read (default None).

        Returns
        -------
        pandas.DataFrame
            The features as a dataframe.

        """
        raise_error(
            msg="Concrete classes need to implement read_df().",
            klass=NotImplementedError,
        )

    @abstractmethod
    def store_metadata(self, meta_md5: str, element: Dict, meta: Dict) -> None:
        """Store metadata.

        Parameters
        ----------
        meta_md5 : str
            The metadata MD5 hash.
        element : dict
            The element as a dictionary.
        meta : dict
            The metadata as a dictionary.
        """
        raise_error(
            msg="Concrete classes need to implement store_metadata().",
            klass=NotImplementedError,
        )

    def store(self, kind: str, **kwargs) -> None:
        """Store extracted features data.

        Parameters
        ----------
        kind : {"matrix", "timeseries", "table"}
            The storage kind.
        **kwargs
            The keyword arguments.

        Raises
        ------
        ValueError
            If ``kind`` is invalid.

        """
        # Do the check before calling the abstract methods, otherwise the
        # meta might be stored even if the data is not stored.
        if kind not in self._valid_inputs:
            raise_error(
                msg=f"I don't know how to store {kind}.",
                klass=ValueError,
            )
        t_meta = kwargs.pop("meta")
        meta_md5, t_meta, t_element = process_meta(t_meta)
        self.store_metadata(meta_md5=meta_md5, element=t_element, meta=t_meta)
        if kind == "matrix":
            self.store_matrix(meta_md5=meta_md5, element=t_element, **kwargs)
        elif kind == "timeseries":
            self.store_timeseries(
                meta_md5=meta_md5, element=t_element, **kwargs
            )
        elif kind == "table":
            self.store_table(meta_md5=meta_md5, element=t_element, **kwargs)

    def store_matrix(
        self,
        meta_md5: str,
        element: Dict,
        data: np.ndarray,
        col_names: Optional[Iterable[str]] = None,
        row_names: Optional[Iterable[str]] = None,
        matrix_kind: Optional[str] = "full",
        diagonal: bool = True,
    ) -> None:
        """Store matrix.

        Parameters
        ----------
        meta_md5 : str
            The metadata MD5 hash.
        element : dict
            The element as a dictionary.
        data : numpy.ndarray
            The matrix data to store.
        col_names : list or tuple of str, optional
            The column names (default None).
        row_names : str, optional
            The column name to use in case number of rows greater than 1.
            If None and number of rows greater than 1, then the name will be
            "index" (default None).
        matrix_kind : str, optional
            The kind of matrix:

            * ``triu`` : store upper triangular only
            * ``tril`` : store lower triangular
            * ``full`` : full matrix

            (default "full").
        diagonal : bool, optional
            Whether to store the diagonal. If `matrix_kind` is "full", setting
            this to False will raise an error (default True).
        """
        raise_error(
            msg="Concrete classes need to implement store_matrix2d().",
            klass=NotImplementedError,
        )

    def store_table(
        self,
        meta_md5: str,
        element: Dict,
        data: Union[np.ndarray, List],
        columns: Optional[Iterable[str]] = None,
        rows_col_name: Optional[str] = None,
    ) -> None:
        """Store table.

        Parameters
        ----------
        meta_md5 : str
            The metadata MD5 hash.
        element : dict
            The element as a dictionary.
        data : numpy.ndarray or list
            The table data to store.
        columns : list or tuple of str, optional
            The columns (default None).
        rows_col_name : str, optional
            The column name to use in case number of rows greater than 1.
            If None and number of rows greater than 1, then the name will be
            "index" (default None).
        """
        raise_error(
            msg="Concrete classes need to implement store_table().",
            klass=NotImplementedError,
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
        raise_error(
            msg="Concrete classes need to implement store_timeseries().",
            klass=NotImplementedError,
        )

    @abstractmethod
    def collect(self) -> None:
        """Collect data."""
        raise_error(
            msg="Concrete classes need to implement collect().",
            klass=NotImplementedError,
        )

    def __str__(self) -> str:
        """Represent object as string.

        Returns
        -------
        str
            The string representation.

        """
        single = (
            "(single output)"
            if self.single_output is True
            else "(multiple output)"
        )
        return f"<{self.__class__.__name__} @ {self.uri} {single}>"
