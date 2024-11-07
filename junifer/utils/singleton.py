"""Provide a singleton class to be used by pipeline components."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from abc import ABCMeta
from typing import Any, Dict, Type


__all__ = ["Singleton"]


class Singleton(type):
    """Make a class singleton.

    Parameters
    ----------
    cls : class
        The class to designate as singleton.

    """

    instances: Dict = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> Type:
        """Get the only instance for a class.

        Parameters
        ----------
        *args : tuple
            The positional arguments to pass to the class.
        **kwargs : dict
            The keyword arguments to pass to the class.

        Returns
        -------
        class
            The only instance of the class.

        """
        if cls not in cls.instances:
            cls.instances[cls] = super(Singleton, cls).__call__(
                *args, **kwargs
            )

        return cls.instances[cls]


class ABCSingleton(ABCMeta, Singleton):
    pass