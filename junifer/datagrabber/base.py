"""Provide abstract base class for DataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Iterator, List, Tuple, Union

from ..pipeline import UpdateMetaMixin
from ..utils import logger, raise_error
from .utils import validate_types


class BaseDataGrabber(ABC, UpdateMetaMixin):
    """Abstract base class for DataGrabber.

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
        # Validate types
        validate_types(types)
        self.types = types

        # Convert str to Path
        if not isinstance(datadir, Path):
            datadir = Path(datadir)
        self._datadir = datadir

        logger.debug("Initializing BaseDataGrabber")
        logger.debug(f"\t_datadir = {datadir}")
        logger.debug(f"\ttypes = {types}")

    def __iter__(self) -> Iterator:
        """Enable iterable support.

        Yields
        ------
        object
            An element that can be indexed by the DataGrabber.

        """
        yield from self.get_elements()

    def __getitem__(self, element: Union[str, Tuple[str]]) -> Dict[str, Dict]:
        """Enable indexing support.

        Parameters
        ----------
        element : str or tuple of str
            The element to be indexed.

        Returns
        -------
        dict
            Dictionary of paths for each type of data required for the
            specified element.

        """
        logger.info(f"Getting element {element}")
        # Convert element to tuple if not already
        if not isinstance(element, tuple):
            element = (element,)
        # Zip through element keys and actual values to construct element
        # access dictionary
        named_element: Dict = dict(zip(self.get_element_keys(), element))
        logger.debug(f"Named element: {named_element}")
        # Fetch element
        out = self.get_item(**named_element)
        # Update metadata
        for _, t_val in out.items():
            self.update_meta(t_val, "datagrabber")
            t_val["meta"]["element"] = named_element

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

    @property
    def datadir(self) -> Path:
        """Get data directory path.

        Returns
        -------
        pathlib.Path
            Path to the data directory. Can be overridden by subclasses.

        """
        return self._datadir

    def filter(self, selection: List[Union[str, Tuple[str]]]) -> Iterator:
        """Filter elements to be grabbed.

        Parameters
        ----------
        selection : list of str or tuple
            The list of partial element key values to filter using.

        Yields
        ------
        object
            An element that can be indexed by the DataGrabber.

        """

        def filter_func(element: Union[str, Tuple[str]]) -> bool:
            """Filter element based on selection.

            Parameters
            ----------
            element : str or tuple of str
                The element to be filtered.

            Returns
            -------
            bool
                If the element passes the filter or not.

            """
            # Convert element to tuple
            if not isinstance(element, tuple):
                element = (element,)
            # Filter based on selection kind
            if isinstance(selection[0], str):
                for opt in selection:
                    if opt in element:
                        return True
            elif isinstance(selection[0], tuple):
                for opt in selection:
                    if set(opt).issubset(element):
                        return True
            return False

        yield from filter(filter_func, self.get_elements())

    @abstractmethod
    def get_element_keys(self) -> List[str]:
        """Get element keys.

        For each item in the ``element`` tuple passed to ``__getitem__()``,
        this method returns the corresponding key(s).

        Returns
        -------
        list of str
            The element keys.

        """
        raise_error(
            msg="Concrete classes need to implement get_element_keys().",
            klass=NotImplementedError,
        )

    @abstractmethod
    def get_elements(self) -> List[Union[str, Tuple[str]]]:
        """Get elements.

        Returns
        -------
        list
            List of elements that can be grabbed. The elements can be strings,
            tuples or any object that will be then used as a key to index the
            DataGrabber.

        """
        raise_error(
            msg="Concrete classes need to implement get_elements().",
            klass=NotImplementedError,
        )

    @abstractmethod
    def get_item(self, **element: Dict) -> Dict[str, Dict]:
        """Get the specified item from the dataset.

        Parameters
        ----------
        element : dict
            The element to be indexed.

        Returns
        -------
        dict
            Dictionary of paths for each type of data required for the
            specified element.

        """
        raise_error(
            msg="Concrete classes need to implement get_item().",
            klass=NotImplementedError,
        )
