"""Provide abstract base class for DataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from abc import ABC, abstractmethod
from collections.abc import Iterator
from enum import Enum
from pathlib import Path
from typing import Annotated, Any

import structlog
from aenum import Enum as AEnum
from pydantic import BaseModel, BeforeValidator, ConfigDict

from ..pipeline import UpdateMetaMixin
from ..typing import Element, Elements
from ..utils import ensure_list, raise_error


__all__ = ["BaseDataGrabber", "DataType"]

_log = structlog.get_logger("junifer")
logger = _log.bind(pkg="datagrabber", step="datagrabber")


class DataType(str, AEnum):
    """Accepted data type."""

    T1w = "T1w"
    T2w = "T2w"
    BOLD = "BOLD"
    Warp = "Warp"
    VBM_GM = "VBM_GM"
    VBM_WM = "VBM_WM"
    VBM_CSF = "VBM_CSF"
    FALFF = "fALFF"
    GCOR = "GCOR"
    LCOR = "LCOR"
    DWI = "DWI"
    FreeSurfer = "FreeSurfer"


def _matches(element: Element, selector: Element) -> bool:
    """Check whether an element matches a selector.

    Parameters
    ----------
    element : ``Element``
        The element.
    selector : ``Element``
        The partial or complete element selector: a value (the element must
        have it) or a tuple of values (the element must have all of them).

    Returns
    -------
    bool
        Whether the element matches the selector.

    """
    if not isinstance(element, tuple):
        element = (element,)
    if isinstance(selector, tuple):
        return set(selector).issubset(element)
    return selector in element


def _selectors_as_tuples(selection: Elements) -> list[tuple]:
    """Get the element selectors as tuples, checking they have the same size.

    Parameters
    ----------
    selection : ``Elements``
        The list of partial or complete element selectors.

    Returns
    -------
    list of tuple
        The selectors, as tuples (a single value is a tuple of one value).

    Raises
    ------
    ValueError
        If the selectors have different numbers of values.

    """
    selectors = [s if isinstance(s, tuple) else (s,) for s in selection]
    if len({len(selector) for selector in selectors}) > 1:
        raise_error(
            msg=(
                "The element selectors must have the same number of values: "
                f"{selection}"
            ),
            klass=ValueError,
        )
    return selectors


class BaseDataGrabber(BaseModel, ABC, UpdateMetaMixin):
    """Abstract base class for data fetcher.

    For every datagrabber, one needs to provide a concrete
    implementation of this abstract class.

    Parameters
    ----------
    types : :enum:`.DataType` or list of variants
        The data type(s) to grab.
    datadir : pathlib.Path
        The path where the data is or will be stored.

    """

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    types: Annotated[
        DataType | list[DataType],
        BeforeValidator(ensure_list),
    ]
    datadir: Path

    def model_post_init(self, context: Any):  # noqa: D102
        # Run extra validation for datagrabbers and fail early if needed
        self.validate_datagrabber_params()
        # Convert to correct data type
        self.types = [
            DataType(t) if isinstance(t, str) else t for t in self.types
        ]
        logger.info(
            f"Parameters: {self.model_dump(mode='json')}",
            component=self.__class__.__name__,
        )

    def validate_datagrabber_params(self) -> None:
        """Run extra logical validation for datagrabber.

        Subclasses can override to provide validation.
        """
        pass

    def __iter__(self) -> Iterator[Elements]:
        """Enable iterable support.

        Yields
        ------
        object
            An element that can be indexed by the DataGrabber.

        """
        yield from self.get_elements()

    def __getitem__(self, element: Element) -> dict[str, dict]:
        """Enable indexing support.

        Parameters
        ----------
        element : `Element`
            The element to be indexed.

        Returns
        -------
        dict
            Dictionary of paths for each type of data required for the
            specified element.

        """
        # Convert element to tuple if not already and extract enum values if
        # present
        element = (
            (element,)
            if not isinstance(element, tuple)
            else tuple(i.value if isinstance(i, Enum) else i for i in element)
        )
        logger.info(f"Getting element {element}")
        # Zip through element keys and actual values to construct element
        # access dictionary
        named_element: dict = dict(
            zip(self.get_element_keys(), element, strict=False)
        )
        logger.debug(f"Named element: {named_element}")
        self._check_element(named_element)
        # Fetch element
        out = self.get_item(**named_element)
        # Update metadata: the element being processed and the keys of the
        # element that the data of each data type depends on
        for t_type, t_val in out.items():
            self.update_meta(t_val, "datagrabber")
            element_keys = self.get_type_element_keys(t_type)
            # Conditional for list dtype vals like Warp
            for entry in t_val if isinstance(t_val, list) else [t_val]:
                entry["meta"]["element"] = named_element
                entry["meta"]["_element_keys"] = element_keys

        return out

    def get_type_element_keys(self, data_type: str) -> list[str]:
        """Get the element keys that the data of a data type depends on.

        The element keys (see :meth:`.get_element_keys`) are the keys that
        the data types to grab depend on.

        Parameters
        ----------
        data_type : str
            The data type.

        Returns
        -------
        list of str
            The element keys, all of them unless a subclass knows which ones
            the data type depends on (e.g., only the subject for data that is
            the same for all the tasks of a subject).

        """
        return self.get_element_keys()

    def _check_element(self, element: dict) -> None:
        """Check the element can be grabbed.

        Parameters
        ----------
        element : dict
            The element, as given to :meth:`.get_item`.

        """

    def __enter__(self) -> "BaseDataGrabber":
        """Context entry."""
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        """Context exit."""
        return None

    def get_types(self) -> list[str]:
        """Get types.

        Returns
        -------
        list of str
            The data type(s) to grab.

        """
        return [x.value if isinstance(x, Enum) else x for x in self.types]

    @property
    def fulldir(self) -> Path:
        """Get complete data directory path.

        Returns
        -------
        pathlib.Path
            Complete path to the data directory.
            Can be overridden by subclasses.

        """
        return self.datadir

    def filter(self, selection: Elements) -> Iterator:
        """Filter elements to be grabbed.

        Parameters
        ----------
        selection : ``Elements``
            The list of partial or complete element selectors to filter using,
            with the same number of values.

        Yields
        ------
        object
            An element that can be indexed by the DataGrabber.

        Raises
        ------
        ValueError
            If the selectors have different numbers of values.

        """
        selectors = _selectors_as_tuples(selection)
        for element in self.get_elements():
            if any(_matches(element, selector) for selector in selectors):
                yield element

    def select_elements(self, selection: Elements) -> list[Element]:
        """Select the elements to grab.

        All the selectors must have the same number of values (a single value
        counts as a tuple of one value), so they are either all complete
        elements or all partial selectors:

        * Complete elements have a value for each element key, in the order of
          :meth:`.get_element_keys`, e.g., ``("sub-01", "rest")`` for the keys
          ``["subject", "task"]``. They are the elements to grab, so the
          elements of the dataset are not needed (they are not searched for).
          Repeated elements are only returned once.
        * Partial selectors have fewer values, e.g., ``"sub-01"`` or
          ``("sub-01",)``. They select the elements of the dataset that match
          them, i.e., that have all their values for any key (see
          :meth:`.filter`). The elements of the dataset are searched for once,
          and each element is returned once, even if several selectors match
          it: with ``["sub-01", "rest"]``, the element ``("sub-01", "rest")``
          matches both selectors and is returned once, together with the other
          tasks of ``sub-01`` and the ``rest`` task of the other subjects.

        Parameters
        ----------
        selection : ``Elements``
            The list of partial or complete element selectors.

        Returns
        -------
        list of tuple
            The selected elements, without duplicates.

        Raises
        ------
        ValueError
            If the selectors have different numbers of values.
        RuntimeError
            If a partial selector does not match any element.

        """
        selectors = _selectors_as_tuples(selection)
        if not selectors:
            return []
        # Complete elements: the selectors are the elements, without the
        # repeated ones
        if len(selectors[0]) == len(self.get_element_keys()):
            # Remove the repeated selectors, keeping the order
            return list(dict.fromkeys(selectors))
        # Partial selectors: the elements of the dataset that match them, in a
        # single pass over the elements. Each element is checked once, so it
        # is returned once even if several selectors match it
        selected = []
        matched = set()
        for element in self.get_elements():
            t_matched = [
                i
                for i, selector in enumerate(selectors)
                if _matches(element, selector)
            ]
            if t_matched:
                selected.append(element)
                matched.update(t_matched)
        # The selectors that no element matches
        invalid = [
            given for i, given in enumerate(selection) if i not in matched
        ]
        if invalid:
            raise_error(
                msg=f"The following element selectors are invalid:\n{invalid}",
                klass=RuntimeError,
            )
        return selected

    @abstractmethod
    def get_element_keys(self) -> list[str]:
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
        )  # pragma: no cover

    @abstractmethod
    def get_elements(self) -> Elements:
        """Get elements.

        Returns
        -------
        list
            List of elements that can be grabbed. The elements can be strings
            or tuples of strings to index the DataGrabber.

        """
        raise_error(
            msg="Concrete classes need to implement get_elements().",
            klass=NotImplementedError,
        )  # pragma: no cover

    @abstractmethod
    def get_item(self, **element: dict) -> dict[str, dict]:
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
        )  # pragma: no cover
