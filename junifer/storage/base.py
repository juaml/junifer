"""Provide abstract base class for feature storage."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from abc import ABC, abstractmethod
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Optional, Union

import numpy as np
import pandas as pd

from ..utils import raise_error
from .utils import process_meta


__all__ = ["BaseFeatureStorage"]


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

    Raises
    ------
    ValueError
        If required storage type(s) is(are) missing from ``storage_types``.

    """

    def __init__(
        self,
        uri: Union[str, Path],
        storage_types: Union[list[str], str],
        single_output: bool = True,
    ) -> None:
        self.uri = uri
        # Convert storage_types to list
        if not isinstance(storage_types, list):
            storage_types = [storage_types]
        # Check if required inputs are found
        if any(x not in self.get_valid_inputs() for x in storage_types):
            wrong_storage_types = [
                x for x in storage_types if x not in self.get_valid_inputs()
            ]
            raise_error(
                f"{self.__class__.__name__} cannot store {wrong_storage_types}"
            )
        self._valid_inputs = storage_types
        self.single_output = single_output

    def get_valid_inputs(self) -> list[str]:
        """Get valid storage types for input.

        Returns
        -------
        list of str
            The list of storage types that can be used as input for this
            storage interface.

        """
        raise_error(
            msg="Concrete classes need to implement get_valid_inputs().",
            klass=NotImplementedError,
        )

    def validate(self, input_: list[str]) -> None:
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
    def list_features(self) -> dict[str, dict[str, Any]]:
        """List the features in the storage.

        Returns
        -------
        dict
            List of features in the storage. The keys are the feature MD5 to
            be used in :meth:`.read_df` and the values are the metadata of each
            feature.

        """
        raise_error(
            msg="Concrete classes need to implement list_features().",
            klass=NotImplementedError,
        )

    @abstractmethod
    def read(
        self,
        feature_name: Optional[str] = None,
        feature_md5: Optional[str] = None,
    ) -> dict[
        str, Union[str, list[Union[int, str, dict[str, str]]], np.ndarray]
    ]:
        """Read stored feature.

        Parameters
        ----------
        feature_name : str, optional
            Name of the feature to read (default None).
        feature_md5 : str, optional
            MD5 hash of the feature to read (default None).

        Returns
        -------
        dict
            The stored feature as a dictionary.

        """
        raise_error(
            msg="Concrete classes need to implement read().",
            klass=NotImplementedError,
        )

    @abstractmethod
    def read_df(
        self,
        feature_name: Optional[str] = None,
        feature_md5: Optional[str] = None,
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
    def store_metadata(self, meta_md5: str, element: dict, meta: dict) -> None:
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
        kind : {"matrix", "timeseries", "vector", "scalar_table"}
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
        elif kind == "vector":
            self.store_vector(meta_md5=meta_md5, element=t_element, **kwargs)
        elif kind == "scalar_table":
            self.store_scalar_table(
                meta_md5=meta_md5, element=t_element, **kwargs
            )
        elif kind == "timeseries_2d":
            self.store_timeseries_2d(
                meta_md5=meta_md5, element=t_element, **kwargs
            )

    def store_matrix(
        self,
        meta_md5: str,
        element: dict,
        data: np.ndarray,
        col_names: Optional[Iterable[str]] = None,
        row_names: Optional[Iterable[str]] = None,
        matrix_kind: str = "full",
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
            The column labels (default None).
        row_names : str, optional
            The row labels (default None).
        matrix_kind : str, optional
            The kind of matrix:

            * ``triu`` : store upper triangular only
            * ``tril`` : store lower triangular
            * ``full`` : full matrix

            (default "full").
        diagonal : bool, optional
            Whether to store the diagonal. If ``matrix_kind = full``, setting
            this to False will raise an error (default True).

        """
        raise_error(
            msg="Concrete classes need to implement store_matrix().",
            klass=NotImplementedError,
        )

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
        raise_error(
            msg="Concrete classes need to implement store_vector().",
            klass=NotImplementedError,
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
        raise_error(
            msg="Concrete classes need to implement store_timeseries().",
            klass=NotImplementedError,
        )

    def store_timeseries_2d(
        self,
        meta_md5: str,
        element: dict,
        data: np.ndarray,
        col_names: Optional[Iterable[str]] = None,
        row_names: Optional[Iterable[str]] = None,
    ) -> None:
        """Store 2D timeseries.

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
        row_names : list or tuple of str, optional
            The row labels (default None).

        """
        raise_error(
            msg="Concrete classes need to implement store_timeseries_2d().",
            klass=NotImplementedError,
        )

    def store_scalar_table(
        self,
        meta_md5: str,
        element: dict,
        data: np.ndarray,
        col_names: Optional[Iterable[str]] = None,
        row_names: Optional[Iterable[str]] = None,
        row_header_col_name: Optional[str] = "feature",
    ) -> None:
        """Store table with scalar values.

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
        row_names : str, optional
            The row labels (default None).
        row_header_col_name : str, optional
            The column name for the row header column (default "feature").

        """
        raise_error(
            msg="Concrete classes need to implement store_scalar_table().",
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
