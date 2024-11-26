"""Provide a singleton class to be used by pipeline components."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
#          Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from abc import ABCMeta
from typing import Any, ClassVar


__all__ = ["ABCSingleton", "Singleton"]


class Singleton(type):
    """Make a class singleton.

    Parameters
    ----------
    cls : class
        The class to designate as singleton.

    """

    instances: ClassVar[dict] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> type:
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
            cls.instances[cls] = super(Singleton, cls).__call__(  # noqa: UP008
                *args, **kwargs
            )

        return cls.instances[cls]


class ABCSingleton(ABCMeta, Singleton):
    """Make an abstract class a singleton."""

    pass
