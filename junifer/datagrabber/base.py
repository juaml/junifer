"""Provide abstract base class for datagrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Iterator, List, Tuple, Union

from ..utils import logger, raise_error
from .utils import validate_types


class BaseDataGrabber(ABC):
    """Abstract base class for datagrabber.

    For every interface that is required, one needs to provide a concrete
    implementation of this abstract class.

    Parameters
    ----------
    types : list of str
        The types of data to be grabbed.
    datadir : str or pathlib.Path
        The directory where the data is / will be stored.

    Attributes
    ----------
    datadir : pathlib.Path
        The directory where the data is / will be stored.

    """

    def __init__(self, types: List[str], datadir: Union[str, Path]) -> None:
        """Initialize the class."""
        # Validate types
        validate_types(types)
        # Convert str to Path
        if not isinstance(datadir, Path):
            datadir = Path(datadir)

        logger.debug("Initializing BaseDataGrabber")
        logger.debug(f"\t_datadir = {datadir}")
        logger.debug(f"\ttypes = {types}")
        self._datadir = datadir
        self.types = types

    def __iter__(self) -> Iterator:
        """Enable iterable support.

        Yields
        ------
        object
            An element that can be indexed by the datagrabber.

        """
        for elem in self.get_elements():
            yield elem

    def __getitem__(self, element: Union[str, Tuple]) -> Dict[str, Dict]:
        """Enable indexing support.

        Parameters
        ----------
        element : str or tuple
            The element to be indexed. If one string is provided, it is
            assumed to be a tuple with only one item. If a tuple is provided,
            each item in the tuple is the value for the replacement string
            specified in "replacements".

        Returns
        -------
        dict
            Dictionary of paths for each type of data required for the
            specified element.

        """
        logger.info(f"Getting element {element}")
        out = {}
        out["meta"] = {"datagrabber": self.get_meta()}
        return out

    def __enter__(self) -> "BaseDataGrabber":
        """Context entry."""
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        """Context exit."""
        return None

    def get_types(self) -> List[str]:
        """Get types.

        Returns
        -------
        list of str
            The types of data to be grabbed.

        """
        return self.types.copy()

    def get_meta(self) -> Dict:
        """Get metadata.

        Returns
        -------
        dict
            The metadata as dictionary.

        """
        t_meta = {}
        t_meta["class"] = self.__class__.__name__
        for k, v in vars(self).items():
            if not k.startswith("_"):
                t_meta[k] = v
        return t_meta

    # TODO: what is the final functionality?
    def get_element_keys(self) -> str:
        """Get element keys.

        Returns
        -------
        str

        """
        return "element"

    @property
    def datadir(self) -> Path:
        """Get data directory path.

        Returns
        -------
        pathlib.Path
            Path to the data directory. Can be overridden by subclasses.

        """
        return self._datadir

    @abstractmethod
    def get_elements(self) -> List:
        """Get elements.

        Returns
        -------
        list
            List of elements that can be grabbed. The elements can be strings,
            tuples or any object that will be then used as a key to index the
            datagrabber.

        """
        raise_error(
            msg="Concrete classes need to implement get_elements().",
            klass=NotImplementedError,
        )
