# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL
from . pipeline import register


def register_datagrabber(klass):
    """Datagrabber decorator.

    Registers the datagrabber so it can be used by name in the pipeline.

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
