"""Provide imports for data sub-package."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from .parcellations import (
    list_parcellations,
    register_parcellation,
    load_parcellation,
)
from .coordinates import (
    list_coordinates,
    register_coordinates,
    load_coordinates,
)
