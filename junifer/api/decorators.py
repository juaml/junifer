"""Provide decorators for api."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Type

from ..pipeline.registry import register


def register_datagrabber(klass: Type) -> Type:
    """Register DataGrabber.

    Registers the DataGrabber so it can be used by name.

    Parameters
    ----------
    klass: class
        The class of the DataGrabber to register.

    Returns
    -------
    klass: class
        The unmodified input class.

    Notes
    -----
    It should only be used as a decorator.

    """
    register(
        step="datagrabber",
        name=klass.__name__,
        klass=klass,
    )
    return klass


def register_datareader(klass: Type) -> Type:
    """Register DataReader.

    Registers the DataReader so it can be used by name.

    Parameters
    ----------
    klass: class
        The class of the DataReader to register.

    Returns
    -------
    klass: class
        The unmodified input class.

    Notes
    -----
    It should only be used as a decorator.

    """
    register(
        step="datareader",
        name=klass.__name__,
        klass=klass,
    )
    return klass


def register_preprocessor(klass: Type) -> Type:
    """Preprocessor registration decorator.

    Registers the preprocessor so it can be used by name.

    Parameters
    ----------
    klass: class
        The class of the preprocessor to register.

    Returns
    -------
    klass: class
        The unmodified input class.

    """
    register(
        step="preprocessing",
        name=klass.__name__,
        klass=klass,
    )
    return klass


def register_marker(klass: Type) -> Type:
    """Marker registration decorator.

    Registers the marker so it can be used by name.

    Parameters
    ----------
    klass: class
        The class of the marker to register.

    Returns
    -------
    klass: class
        The unmodified input class.

    """
    register(
        step="marker",
        name=klass.__name__,
        klass=klass,
    )
    return klass


def register_storage(klass: Type) -> Type:
    """Storage registration decorator.

    Registers the storage so it can be used by name.

    Parameters
    ----------
    klass: class
        The class of the storage to register.

    Returns
    -------
    klass: class
        The unmodified input class.

    """
    register(
        step="storage",
        name=klass.__name__,
        klass=klass,
    )
    return klass
