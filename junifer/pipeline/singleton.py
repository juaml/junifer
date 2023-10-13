"""Provide a singleton class to be used by pipeline components."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Any, Dict, Type


def singleton(cls: Type) -> Type:
    """Make a class singleton.

    Parameters
    ----------
    cls : class
        The class to designate as singleton.

    Returns
    -------
    class
        The only instance of the class.

    """
    instances: Dict = {}

    def get_instance(*args: Any, **kwargs: Any) -> Type:
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
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance
