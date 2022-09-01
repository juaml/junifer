"""Provide abstract base class for multiple source datagrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import Dict, List, Tuple, Union

from .base import BaseDataGrabber


class MultipleDataGrabber(BaseDataGrabber):
    """Abstract base class for data fetching from multiple sources.

    Defines a DataGrabber which can be used to fetch data from multiple
    sources.

    Parameters
    ----------
    datagrabbers : list of datagrabbers
        The datagrabbers to use to fetch data using.
    **kwargs
        Keyword arguments passed to superclass.

    """

    def __init__(self, datagrabbers: List[BaseDataGrabber], **kwargs) -> None:
        """Initialize the class."""
        # TODO: Check datagrabbers consistency
        # - same element keys
        # - no overlapping types
        self._datagrabbers = datagrabbers

    def __getitem__(self, element: Union[str, Tuple]) -> Dict[str, Path]:
        """Implement indexing.

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
        out = {}
        for dg in self._datagrabbers:
            t_out = dg[element]
            out.update(t_out)
        return out

    def __enter__(self) -> "BaseDataGrabber":
        """Implement context entry."""
        for dg in self._datagrabbers:
            dg.__enter__()

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        """Implement context exit."""
        for dg in self._datagrabbers:
            dg.__exit__(exc_type, exc_value, exc_traceback)

    def get_types(self) -> List[List[str]]:
        """Get types.

        Returns
        -------
        list of list of str
            The types of data to be grabbed.

        """
        types = [x for dg in self._datagrabbers for x in dg.get_types()]
        return types

    def get_meta(self) -> Dict:
        """Get metadata.

        Returns
        -------
        dict
            The metadata as dictionary.

        """
        t_meta = {}
        t_meta["class"] = self.__class__.__name__
        t_meta["datagrabbers"] = [dg.get_meta() for dg in self._datagrabbers]
