"""Provide abstract base class for multiple source datagrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Dict, List, Tuple, Union

from .base import BaseDataGrabber


class MultipleDataGrabber(BaseDataGrabber):
    """Data Grabber class for data fetching from multiple sources.

    Defines a Data Grabber which can be used to fetch data from multiple
    datagrabbers.

    Parameters
    ----------
    datagrabbers : list of datagrabber-like objects
        The datagrabbers to use to fetch data using.
    **kwargs
        Keyword arguments passed to superclass.
    """

    def __init__(self, datagrabbers: List[BaseDataGrabber], **kwargs) -> None:
        # Check datagrabbers consistency
        # 1) same element keys
        first_keys = datagrabbers[0].get_element_keys()
        for dg in datagrabbers[1:]:
            if dg.get_element_keys() != first_keys:
                raise ValueError("Datagrabbers have different element keys.")
        # 2) no overlapping types
        types = [x for dg in datagrabbers for x in dg.get_types()]
        if len(types) != len(set(types)):
            raise ValueError("Datagrabbers have overlapping types.")
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

    def get_item(self, **element: Dict) -> Dict[str, Dict]:
        """Get item.

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
        raise NotImplementedError(
            "get_item() is not useful for this class, hence not implemented."
        )

    def __enter__(self) -> "BaseDataGrabber":
        """Implement context entry."""
        for dg in self._datagrabbers:
            dg.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        """Implement context exit."""
        for dg in self._datagrabbers:
            dg.__exit__(exc_type, exc_value, exc_traceback)

    def get_elements(self) -> List:
        """Get elements.

        Returns
        -------
        list
            The list of elements that can be grabbed in the dataset. It
            corresponds to the elements that are present in all the
            related datagrabbers.
        """
        all_elements = [dg.get_elements() for dg in self._datagrabbers]
        elements = set(all_elements[0])
        for s in all_elements[1:]:
            elements.intersection_update(s)
        return list(elements)

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

    def get_types(self) -> List[str]:
        """Get types.

        Returns
        -------
        list of list of str
            The types of data to be grabbed.

        """
        types = [x for dg in self._datagrabbers for x in dg.get_types()]
        return types
