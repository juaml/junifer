"""Provide dispatch functions for pipeline data registries."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

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


if TYPE_CHECKING:
    from nibabel.nifti1 import Nifti1Image


__all__ = [
    "deregister_data",
    "get_data",
    "list_data",
    "load_data",
    "register_data",
]


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

    if kind == "coordinates":
        return CoordinatesRegistry().get(
            coords=names,
            target_data=target_data,
            extra_input=extra_input,
        )
    elif kind == "parcellation":
        return ParcellationRegistry().get(
            parcellations=names,
            target_data=target_data,
            extra_input=extra_input,
        )
    elif kind == "mask":
        return MaskRegistry().get(
            masks=names,
            target_data=target_data,
            extra_input=extra_input,
        )
    else:
        raise_error(f"Unknown data kind: {kind}")


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

    if kind == "coordinates":
        return CoordinatesRegistry().list
    elif kind == "parcellation":
        return ParcellationRegistry().list
    elif kind == "mask":
        return MaskRegistry().list
    else:
        raise_error(f"Unknown data kind: {kind}")


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

    if kind == "coordinates":
        return CoordinatesRegistry().load(name=name)
    elif kind == "parcellation":
        return ParcellationRegistry().load(name=name, **kwargs)
    elif kind == "mask":
        return MaskRegistry().load(name=name, **kwargs)
    else:
        raise_error(f"Unknown data kind: {kind}")


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

    if kind == "coordinates":
        return CoordinatesRegistry().register(
            name=name, space=space, overwrite=overwrite, **kwargs
        )
    elif kind == "parcellation":
        return ParcellationRegistry().register(
            name=name, space=space, overwrite=overwrite, **kwargs
        )
    elif kind == "mask":
        return MaskRegistry().register(
            name=name, space=space, overwrite=overwrite, **kwargs
        )
    else:
        raise_error(f"Unknown data kind: {kind}")


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

    if kind == "coordinates":
        return CoordinatesRegistry().deregister(name=name)
    elif kind == "parcellation":
        return ParcellationRegistry().deregister(name=name)
    elif kind == "mask":
        return MaskRegistry().deregister(name=name)
    else:
        raise_error(f"Unknown data kind: {kind}")
