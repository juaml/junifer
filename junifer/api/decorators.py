"""Provide decorators for api."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from .registry import register


def register_datagrabber(klass: type) -> type:
    """Datagrabber registration decorator.

    Registers the datagrabber so it can be used by name.

    Parameters
    ----------
    klass: class
        The class of the datagrabber to register.

    Returns
    -------
    klass: class
        The unmodified input class.

    """
    register(
        step="datagrabber",
        name=klass.__name__,
        klass=klass,
    )
    return klass


def register_marker(klass: type) -> type:
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


def register_storage(klass):
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
