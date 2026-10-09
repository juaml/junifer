"""Provide concrete implementation for multi sourced DataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from collections import defaultdict
from pathlib import Path
from typing import Annotated

from pydantic import BeforeValidator, ConfigDict

from ..api.decorators import register_datagrabber
from ..typing import DataGrabberLike, Element
from ..utils import deep_update, ensure_list, raise_error
from .base import BaseDataGrabber, DataType
from .pattern import PatternDataGrabber, _join_elements
from .pattern_datalad import PatternDataladDataGrabber


__all__ = ["MultipleDataGrabber"]


def _nested_types_only(
    datagrabber: DataGrabberLike, data_type: str
) -> list[str] | None:
    """Get the nested data types grabbed without the main file of a data type.

    Parameters
    ----------
    datagrabber : DataGrabber-like object
        The DataGrabber.
    data_type : str
        The data type.

    Returns
    -------
    list of str or None
        The nested data types (e.g., ``["confounds"]``) if the DataGrabber
        only grabs them, without the main file of the data type, or None if
        it grabs the main file.

    """
    patterns = getattr(datagrabber, "patterns", None)
    if patterns is None:
        return None
    dtype_val = patterns.get(data_type)
    # Data types with a list of patterns (e.g., Warp) have their main files
    if dtype_val is None or isinstance(dtype_val, list):
        return None
    if "pattern" in dtype_val:
        return None
    return [k for k, v in dtype_val.items() if isinstance(v, dict)]


@register_datagrabber
class MultipleDataGrabber(BaseDataGrabber):
    """Concrete implementation for multi sourced data fetching.

    Implements a DataGrabber which can be used to fetch data from multiple
    DataGrabbers, e.g., from different datasets:

    * Each data type is grabbed by one DataGrabber (set with their ``types``),
      except for the DataGrabbers that only grab the nested data types of a
      data type (without its main file, e.g., only the ``confounds`` of
      ``BOLD``), which replace the nested data types of the other one.
    * The element keys are the ones of the first DataGrabber, followed by the
      other keys of the other DataGrabbers, which can have different keys
      (e.g., ``subject`` and ``task`` for ``BOLD``, and only ``subject`` for
      ``VBM_GM``). The keys with the same name must have the same values in
      all the DataGrabbers.
    * The elements are the ones available in all the DataGrabbers, joined on
      their common keys, and each DataGrabber grabs an element with its keys.

    Parameters
    ----------
    datagrabbers : list of DataGrabber-like objects
        The DataGrabbers to use for fetching data.
    **kwargs
        Keyword arguments passed to superclass.

    Raises
    ------
    RuntimeError
        If more than one DataGrabber grabs the main file of a data type or
        the same nested data type without the main file.

    """

    model_config = ConfigDict(extra="allow")

    datagrabbers: list[
        DataGrabberLike | PatternDataGrabber | PatternDataladDataGrabber
    ]
    types: Annotated[
        DataType | list[DataType], BeforeValidator(ensure_list)
    ] = []  # noqa: RUF012
    datadir: Path = Path(".")

    def validate_datagrabber_params(self) -> None:
        """Run extra logical validation for datagrabber."""
        # Each data type is grabbed by one DataGrabber, except for the nested
        # data types grabbed without the main file, which can only be
        # grabbed by one of these DataGrabbers
        main = defaultdict(list)
        nested = defaultdict(list)
        for i, dg in enumerate(self.datagrabbers):
            for data_type in dg.get_types():
                nested_types = _nested_types_only(dg, data_type)
                if nested_types is None:
                    main[data_type].append(i)
                else:
                    for nested_type in nested_types:
                        nested[(data_type, nested_type)].append(i)
        for data_type, dgs in main.items():
            if len(dgs) > 1:
                raise_error(
                    msg=(
                        f"Data type `{data_type}` is grabbed by more than one "
                        f"DataGrabber ({dgs}), it must be removed from the "
                        "`types` of all but one of them"
                    ),
                    klass=RuntimeError,
                )
        for (data_type, nested_type), dgs in nested.items():
            if len(dgs) > 1:
                raise_error(
                    msg=(
                        f"Nested data type `{data_type}.{nested_type}` is "
                        f"grabbed by more than one DataGrabber ({dgs})"
                    ),
                    klass=RuntimeError,
                )

    def __getitem__(self, element: Element) -> dict:
        """Implement indexing.

        Parameters
        ----------
        element : `Element`
            The element to be indexed. If one string is provided, it is
            assumed to be a tuple with only one item. If a tuple is provided,
            each item in the tuple is the value for the element key (see
            :meth:`.get_element_keys`).

        Returns
        -------
        dict
            Dictionary of paths for each type of data required for the
            specified element.

        """
        if not isinstance(element, tuple):
            element = (element,)
        named_element = dict(
            zip(self.get_element_keys(), element, strict=True)
        )
        # Grab the element with the keys of each DataGrabber
        outs = []
        metas = []
        for dg in self.datagrabbers:
            t_element = tuple(named_element[k] for k in dg.get_element_keys())
            outs.append((dg, dg[t_element]))
            # Now get the meta for this datagrabber
            t_meta = {}
            dg.update_meta(t_meta, "datagrabber")
            # Store all the sub-datagrabbers meta
            metas.append(t_meta["meta"]["datagrabber"])

        # Add the data types with their main file first, and then the nested
        # data types grabbed without the main file, which replace the ones
        # grabbed with the main file
        out = {}
        for nested_only in (False, True):
            for dg, t_out in outs:
                for data_type, value in t_out.items():
                    t_nested_only = (
                        _nested_types_only(dg, data_type) is not None
                    )
                    if t_nested_only != nested_only:
                        continue
                    if data_type in out:
                        deep_update(out[data_type], value)
                    else:
                        out[data_type] = value

        # Update all the metas again
        for kind in out:
            to_update = out[kind]
            if not isinstance(to_update, list):
                to_update = [to_update]
            for t_kind in to_update:
                self.update_meta(t_kind, "datagrabber")
                t_kind["meta"]["datagrabber"]["datagrabbers"] = metas
                t_kind["meta"]["element"] = named_element
        return out

    def __enter__(self) -> "MultipleDataGrabber":
        """Implement context entry."""
        for dg in self.datagrabbers:
            dg.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        """Implement context exit."""
        for dg in self.datagrabbers:
            dg.__exit__(exc_type, exc_value, exc_traceback)

    def get_types(self) -> list[str]:
        """Get types.

        Returns
        -------
        list of str
            The types of data to be grabbed.

        """
        types = [x for dg in self.datagrabbers for x in dg.get_types()]
        return list(dict.fromkeys(types))

    def get_element_keys(self) -> list[str]:
        """Get element keys.

        For each item in the ``element`` tuple passed to ``__getitem__()``,
        this method returns the corresponding key(s): the keys of the first
        DataGrabber, followed by the other keys of the other DataGrabbers.

        Returns
        -------
        list of str
            The element keys.

        """
        keys = [k for dg in self.datagrabbers for k in dg.get_element_keys()]
        return list(dict.fromkeys(keys))

    def get_elements(self) -> list:
        """Get elements.

        The elements of the DataGrabbers are joined on their common keys, as
        the elements of the data types of a :class:`.PatternDataGrabber`, so
        the elements are the ones available in all the DataGrabbers.

        Returns
        -------
        list
            List of elements that can be grabbed. The elements can be strings,
            tuples or any object that will be then used as a key to index the
            the DataGrabber. The element should be present in all of the
            related DataGrabbers.

        """
        elements = None
        keys = []
        for dg in self.datagrabbers:
            t_keys = dg.get_element_keys()
            t_elements = {
                e if isinstance(e, tuple) else (e,) for e in dg.get_elements()
            }
            if elements is None:
                elements, keys = t_elements, t_keys
            else:
                elements, keys = _join_elements(
                    elements, keys, t_elements, t_keys
                )
        if elements is None:
            return []
        out = sorted(elements)
        if len(keys) == 1:
            out = [element[0] for element in out]
        return out

    def get_item(self, **_: dict) -> dict[str, dict]:
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
