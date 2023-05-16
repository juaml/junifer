"""Provide concrete implementation for multi sourced DataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Dict, List, Tuple, Union

from ..utils import raise_error
from .base import BaseDataGrabber


class MultipleDataGrabber(BaseDataGrabber):
    """Concrete implementation for multi sourced data fetching.

    Implements a DataGrabber which can be used to fetch data from multiple
    DataGrabbers.

    Parameters
    ----------
    datagrabbers : list of DataGrabber-like objects
        The DataGrabbers to use for fetching data.
    **kwargs
        Keyword arguments passed to superclass.

    """

    def __init__(self, datagrabbers: List[BaseDataGrabber], **kwargs) -> None:
        # Check datagrabbers consistency
        # 1) same element keys
        first_keys = datagrabbers[0].get_element_keys()
        for dg in datagrabbers[1:]:
            if dg.get_element_keys() != first_keys:
                raise_error("DataGrabbers have different element keys.")
        # 2) no overlapping types
        types = [x for dg in datagrabbers for x in dg.get_types()]
        if len(types) != len(set(types)):
            raise_error("DataGrabbers have overlapping types.")
        self._datagrabbers = datagrabbers

    def __getitem__(self, element: Union[str, Tuple]) -> Dict:
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
        metas = []
        for dg in self._datagrabbers:
            t_out = dg[element]
            out.update(t_out)
            # Now get the meta for this datagrabber
            t_meta = {}
            dg.update_meta(t_meta, "datagrabber")
            # Store all the sub-datagrabbers meta
            metas.append(t_meta["meta"]["datagrabber"])

        # Update all the metas again
        for kind in out:
            self.update_meta(out[kind], "datagrabber")
            out[kind]["meta"]["datagrabber"]["datagrabbers"] = metas
        return out

    def __enter__(self) -> "MultipleDataGrabber":
        """Implement context entry."""
        for dg in self._datagrabbers:
            dg.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        """Implement context exit."""
        for dg in self._datagrabbers:
            dg.__exit__(exc_type, exc_value, exc_traceback)

    # TODO: return type should be List[List[str]], but base type is List[str]
    def get_types(self) -> List[str]:
        """Get types.

        Returns
        -------
        list of list of str
            The types of data to be grabbed.

        """
        types = [x for dg in self._datagrabbers for x in dg.get_types()]
        return types

    def get_element_keys(self) -> List[str]:
        """Get element keys.

        For each item in the ``element`` tuple passed to ``__getitem__()``,
        this method returns the corresponding key(s).

        Returns
        -------
        list of str
            The element keys.

        """
        return self._datagrabbers[0].get_element_keys()

    def get_elements(self) -> List:
        """Get elements.

        Returns
        -------
        list
            List of elements that can be grabbed. The elements can be strings,
            tuples or any object that will be then used as a key to index the
            the DataGrabber. The element should be present in all of the
            related DataGrabbers.

        """
        all_elements = [dg.get_elements() for dg in self._datagrabbers]
        elements = set(all_elements[0])
        for s in all_elements[1:]:
            elements.intersection_update(s)
        return list(elements)

    def get_item(self, **_: Dict) -> Dict[str, Dict]:
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

        Notes
        -----
            This function is not implemented for this class as it is useless.

        """
        raise_error(
            msg=(
                "get_item() is not useful for this class, hence not "
                "implemented."
            ),
            klass=NotImplementedError,
        )
