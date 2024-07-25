"""Provide imports for complexity sub-package."""

# Authors: Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from importlib.util import find_spec

from ..utils import raise_error


# Check if neurokit2 is found
if find_spec("neurokit2") is None:
    raise_error(
        msg="Could not find `neurokit2`, make sure the package is installed.",
        klass=ImportError,
    )
else:
    import lazy_loader as lazy

    __getattr__, __dir__, __all__ = lazy.attach_stub(__name__, __file__)
