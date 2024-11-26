"""Provide API decorators."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL


from ..pipeline import PipelineComponentRegistry
from ..typing import DataGrabberLike, MarkerLike, PreprocessorLike, StorageLike


__all__ = [
    "register_datagrabber",
    "register_datareader",
    "register_marker",
    "register_preprocessor",
    "register_storage",
]


def register_datagrabber(klass: DataGrabberLike) -> DataGrabberLike:
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
    PipelineComponentRegistry().register(
        step="datagrabber",
        klass=klass,
    )
    return klass


def register_datareader(klass: type) -> type:
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
    PipelineComponentRegistry().register(
        step="datareader",
        klass=klass,
    )
    return klass


def register_preprocessor(klass: PreprocessorLike) -> PreprocessorLike:
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
    PipelineComponentRegistry().register(
        step="preprocessing",
        klass=klass,
    )
    return klass


def register_marker(klass: MarkerLike) -> MarkerLike:
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
    PipelineComponentRegistry().register(
        step="marker",
        klass=klass,
    )
    return klass


def register_storage(klass: StorageLike) -> StorageLike:
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
    PipelineComponentRegistry().register(
        step="storage",
        klass=klass,
    )
    return klass
