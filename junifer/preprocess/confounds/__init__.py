"""Provide imports for confounds sub-package."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL

import lazy_loader as lazy


__getattr__, __dir__, __all__ = lazy.attach_stub(__name__, __file__)
