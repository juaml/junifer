"""Provide decorators for api."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from .registry import register


def register_datagrabber(klass):
    """Datagrabber decorator.

    Registers the datagrabber so it can be used by name.

    Parameters
    ----------
    klass: class
        The class of the datagrabber to register.

    Returns
    -------
    klass: class
        The unmodified input class
    """
    register('datagrabber', klass.__name__, klass)
    return klass


def register_marker(klass):
    """Marker decorator.

    Registers the marker so it can be used by name.

    Parameters
    ----------
    klass: class
        The class of the marker to register.

    Returns
    -------
    klass: class
        The unmodified input class
    """
    register('marker', klass.__name__, klass)
    return klass


def register_storage(klass):
    """Storage decorator.

    Registers the storage so it can be used by name.

    Parameters
    ----------
    klass: class
        The class of the storage to register.

    Returns
    -------
    klass: class
        The unmodified input class
    """
    register('storage', klass.__name__, klass)
    return klass
