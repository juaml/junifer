"""Provide abstract base class for feature storage."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Union

import pandas as pd

from .._version import __version__
from ..utils import raise_error


class BaseFeatureStorage(ABC):
    """Abstract base class for feature storage.

    For every interface that is required, one needs to provide a concrete
    implementation of this abstract class.

    Parameters
    ----------
    uri : str or pathlib.Path
        The path to the storage.
    single_output : bool, optional
        Whether to have single output (default False).

    """

    def __init__(
        self, uri: Union[str, Path], single_output: bool = False
    ) -> None:
        """Initialize the class."""
        self.uri = uri
        self.single_output = single_output

    def get_meta(self) -> Dict:
        """Get metadata.

        Returns
        -------
        meta : dict
            The metadata as a dictionary.

        """
        meta = {}
        meta["versions"] = {
            "junifer": __version__,
        }
        return meta

    # TODO: is raising ValueError required?
    @abstractmethod
    def validate(self, input_: List[str]) -> bool:
        """Validate the input to the pipeline step.

        Parameters
        ----------
        input_ : list
            The input to the pipeline step.

        Returns
        -------
        bool
            Whether the `input` is valid or not.

        Raises
        ------
        ValueError
            If the input does not have the required data.

        """
        raise_error(
            msg="Concrete classes need to implement validate_input().",
            klass=NotImplementedError,
        )

    @abstractmethod
    def list_features(
        self, return_df: bool = False
    ) -> Union[Dict[str, Dict], pd.DataFrame]:
        """List the features in the storage.

        Parameters
        ----------
        return_df : bool, optional
            If True, returns a pandas DataFrame. If False, returns a
            dictionary (default False).

        Returns
        -------
        dict or pandas.DataFrame
            List of features in the storage. If dictionary is returned, the
            keys are the feature names to be used in read_features() and the
            values are the metadata of each feature.

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
        """Read feature from the storage.

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
    def store_metadata(self, meta: Dict) -> str:
        """Store metadata.

        Parameters
        ----------
        meta : dict
            The metadata as a dictionary.

        Returns
        -------
        str
            The metadata column

        """
        raise_error(
            msg="Concrete classes need to implement store_metadata().",
            klass=NotImplementedError,
        )

    # TODO: complete type annotations
    @abstractmethod
    def store_matrix2d(
        self,
        data,
        meta: Dict,
        col_names: Optional[Iterable[str]] = None,
        row_names: Optional[Iterable[str]] = None,
        kind: Optional[str] = "full",
        diagonal: bool = True,
    ) -> None:
        """Store 2D matrix.

        Parameters
        ----------
        data
        meta : dict
            The metadata as a dictionary.
        col_names : list or tuple of str, optional
            The column names (default None).
        row_names : list of tuple of str, optional
            The row names (default None).
        kind : str, optional
            The kind of matrix:
            - 'triu': store upper triangular only.
            - 'tril': store lower triangular.
            - 'full': full matrix (default 'full').
        diagonal : bool, optional
            Whether to store the diagonal (default True).
            If kind == 'full', setting this to false will raise
            an error

        """
        raise_error(
            msg="Concrete classes need to implement store_matrix2d().",
            klass=NotImplementedError,
        )

    # TODO: complete type annotations
    @abstractmethod
    def store_table(
        self,
        data,
        meta: Dict,
        columns: Optional[Iterable[str]] = None,
        rows_col_name: Optional[str] = None,
    ) -> None:
        """Store table.

        Parameters
        ----------
        data
        meta : dict
            The metadata as a dictionary.
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

    @abstractmethod
    def store_df(self, df: pd.DataFrame, meta: Dict) -> None:
        """Store pandas DataFerame.

        Parameters
        ----------
        df : pandas.DataFrame
            The DataFrame to store.
        meta : dict
            The metadata as a dictionary.

        """
        raise_error(
            msg="Concrete classes need to implement store_df().",
            klass=NotImplementedError,
        )

    # TODO: complete type annotations
    @abstractmethod
    def store_timeseries(self, data, meta: Dict) -> None:
        """Store timeseries.

        Parameters
        ----------
        data
        meta : dict
            The metadata as a dictionary.

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
