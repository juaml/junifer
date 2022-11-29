"""Provide imports for data sub-package."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from .coordinates import (
    list_coordinates,
    load_coordinates,
    register_coordinates,
)
from .parcellations import (
    list_parcellations,
    load_parcellation,
    register_parcellation,
)

from .masks import (
    list_masks,
    load_mask,
    register_mask,
)

from . import utils
