"""Provide abstract base class for feature storage."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Union

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
    storage_types : str or list of str
        The available storage types for the class.
    single_output : bool, optional
        Whether to have single output (default False).

    """

    def __init__(
        self,
        uri: Union[str, Path],
        storage_types: Union[List[str], str],
        single_output: bool = False,
    ) -> None:
        self.uri = uri
        if not isinstance(storage_types, list):
            storage_types = [storage_types]
        self._valid_inputs = storage_types
        self.single_output = single_output

    def get_meta(self) -> Dict:
        """Get metadata.

        Returns
        -------
        dict
            The metadata as a dictionary.

        """
        meta = {}
        meta["versions"] = {
            "junifer": __version__,
        }
        return meta

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
    def store_metadata(self, meta: Dict) -> str:
        """Store metadata.

        Parameters
        ----------
        meta : dict
            The metadata as a dictionary.

        Returns
        -------
        str
            The metadata column.

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
        if kind == "matrix":
            self.store_matrix(**kwargs)
        elif kind == "timeseries":
            self.store_timeseries(**kwargs)
        elif kind == "table":
            self.store_table(**kwargs)
        else:
            raise ValueError(f"I don't know how to store {kind}")

    def store_df(self, **kwargs) -> None:
        """Store pandas DataFrame.

        Parameters
        ----------
        **kwargs : dict
            The keyword arguments.

        """
        raise_error(
            msg="Concrete classes need to implement store_df().",
            klass=NotImplementedError,
        )

    def store_matrix(self, **kwargs) -> None:
        """Store matrix.

        Parameters
        ----------
        **kwargs : dict
            The keyword arguments.

        """
        raise_error(
            msg="Concrete classes need to implement store_matrix2d().",
            klass=NotImplementedError,
        )

    def store_table(self, **kwargs) -> None:
        """Store table.

        Parameters
        ----------
        **kwargs : dict
            The keyword arguments.

        """
        raise_error(
            msg="Concrete classes need to implement store_table().",
            klass=NotImplementedError,
        )

    def store_timeseries(self, **kwargs) -> None:
        """Store timeseries.

        Parameters
        ----------
        **kwargs : dict
            The keyword arguments.

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
