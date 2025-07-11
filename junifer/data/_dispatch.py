"""Provide dispatch functions for pipeline data registries."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from collections.abc import Iterator, MutableMapping
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Optional,
    Union,
)

from numpy.typing import ArrayLike

from ..utils import raise_error
from .coordinates import CoordinatesRegistry
from .masks import MaskRegistry
from .parcellations import ParcellationRegistry
from .pipeline_data_registry_base import BasePipelineDataRegistry


if TYPE_CHECKING:
    from nibabel.nifti1 import Nifti1Image

__all__ = [
    "DataDispatcher",
    "deregister_data",
    "get_data",
    "list_data",
    "load_data",
    "register_data",
]


class DataDispatcher(MutableMapping):
    """Class for helping dynamic data dispatch."""

    _instance = None

    def __new__(cls):
        # Make class singleton
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Set registries
            cls._registries: dict[str, type[BasePipelineDataRegistry]] = {}
            cls._builtin: dict[str, type[BasePipelineDataRegistry]] = {}
            cls._external: dict[str, type[BasePipelineDataRegistry]] = {}
            cls._builtin.update(
                {
                    "coordinates": CoordinatesRegistry,
                    "parcellation": ParcellationRegistry,
                    "mask": MaskRegistry,
                }
            )
            cls._registries.update(cls._builtin)
        return cls._instance

    def __getitem__(self, key: str) -> type[BasePipelineDataRegistry]:
        return self._registries[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._registries)

    def __len__(self) -> int:
        return len(self._registries)

    def __delitem__(self, key: str) -> None:
        # Internal check
        if key in self._builtin:
            raise_error(f"Cannot delete in-built key: {key}")
        # Non-existing key
        if key not in self._external:
            raise_error(klass=KeyError, msg=key)
        # Update external
        _ = self._external.pop(key)
        # Update global
        _ = self._registries.pop(key)

    def __setitem__(
        self, key: str, value: type[BasePipelineDataRegistry]
    ) -> None:
        # Internal check
        if key in self._builtin:
            raise_error(f"Cannot set value for in-built key: {key}")
        # Value type check
        if not issubclass(value, BasePipelineDataRegistry):
            raise_error(f"Invalid value type: {type(value)}")
        # Update external
        self._external[key] = value
        # Update global
        self._registries[key] = value

    def popitem():
        """Not implemented."""
        pass

    def clear(self):
        """Not implemented."""
        pass

    def setdefault(self, key: str, value=None):
        """Not implemented."""
        pass


def get_data(
    kind: str,
    names: Union[
        str,  # coordinates, parcellation, mask
        list[str],  # parcellation, mask
        dict,  # mask
        list[dict],  # mask
    ],
    target_data: dict[str, Any],
    extra_input: Optional[dict[str, Any]] = None,
) -> Union[
    tuple[ArrayLike, list[str]],  # coordinates
    tuple["Nifti1Image", list[str]],  # parcellation
    "Nifti1Image",  # mask
]:
    """Get tailored ``kind`` for ``target_data``.

    Parameters
    ----------
    kind : {"coordinates", "parcellation", "mask"}
        Kind of data to fetch and apply.
    names : str or dict or list of str / dict
        The registered name(s) of the data.
    target_data : dict
        The corresponding item of the data object to which the data
        will be applied.
    extra_input : dict, optional
        The other fields in the data object. Useful for accessing other
        data types that need to be used in the computation of data
        (default None).

    Returns
    -------
    tuple of numpy.ndarray, list of str; \
    tuple of nibabel.nifti1.Nifti1Image, list of str; \
    nibabel.nifti1.Nifti1Image

    Raises
    ------
    ValueError
        If ``kind`` is invalid value.

    """
    try:
        registry = DataDispatcher()[kind]
    except KeyError:
        raise_error(f"Unknown data kind: {kind}")
    else:
        return registry().get(
            names,
            target_data=target_data,
            extra_input=extra_input,
        )


def list_data(kind: str) -> list[str]:
    """List available data for ``kind``.

    Parameters
    ----------
    kind : {"coordinates", "parcellation", "mask"}
        Kind of data registry to list.

    Returns
    -------
    list of str
        Available data for the registry.

    Raises
    ------
    ValueError
        If ``kind`` is invalid value.

    """

    try:
        registry = DataDispatcher()[kind]
    except KeyError:
        raise_error(f"Unknown data kind: {kind}")
    else:
        return registry().list


def load_data(
    kind: str,
    name: str,
    **kwargs,
) -> Union[
    tuple[ArrayLike, list[str], str],  # coordinates
    tuple[Optional["Nifti1Image"], list[str], Path, str],  # parcellation
    tuple[
        Optional[Union["Nifti1Image", Callable]], Optional[Path], str
    ],  # mask
]:
    """Load ``kind`` named ``name``.

    Parameters
    ----------
    kind : {"coordinates", "parcellation", "mask"}
        Kind of data to load.
    name : str
        The registered name of the data.
    **kwargs
        Keyword arguments are passed to respective registry class method.

    Returns
    -------
    tuple of numpy.ndarray, list of str, str; \
    tuple of nibabel.nifti1.Nifti1Image or None, \
    list of str, pathlib.Path, str; \
    tuple of nibabel.nifti1.Nifti1Image or callable or None, \
    pathlib.Path or None, str

    Raises
    ------
    ValueError
        If ``kind`` is invalid value.

    """
    try:
        registry = DataDispatcher()[kind]
    except KeyError:
        raise_error(f"Unknown data kind: {kind}")
    else:
        return registry().load(name, **kwargs)


def register_data(
    kind: str,
    name: str,
    space: str,
    overwrite: bool = False,
    **kwargs,
) -> None:
    """Register ``name`` under ``kind``.

    Parameters
    ----------
    kind : {"coordinates", "parcellation", "mask"}
        Kind of data to register.
    name : str
        The name to register.
    space : str
        The template space of the data.
    overwrite : bool, optional
        If True, overwrite an existing data with the same name.
    **kwargs
        Keyword arguments are passed to respective registry class method.

    Raises
    ------
    ValueError
        If ``kind`` is invalid value.

    """

    try:
        registry = DataDispatcher()[kind]
    except KeyError:
        raise_error(f"Unknown data kind: {kind}")
    else:
        return registry().register(
            name=name, space=space, overwrite=overwrite, **kwargs
        )


def deregister_data(kind: str, name: str) -> None:
    """De-register ``name`` from ``kind``.

    Parameters
    ----------
    kind : {"coordinates", "parcellation", "mask"}
        Kind of data to register.
    name : str
        The name to de-register.

    Raises
    ------
    ValueError
        If ``kind`` is invalid value.

    """

    try:
        registry = DataDispatcher()[kind]
    except KeyError:
        raise_error(f"Unknown data kind: {kind}")
    else:
        return registry().deregister(name=name)
