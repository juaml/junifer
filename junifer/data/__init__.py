"""Provide imports for data sub-package."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from .coordinates import (
    list_coordinates,
    load_coordinates,
    register_coordinates,
    get_coordinates,
)
from .parcellations import (
    list_parcellations,
    load_parcellation,
    register_parcellation,
    merge_parcellations,
    get_parcellation,
)

from .masks import (
    list_masks,
    load_mask,
    register_mask,
    get_mask,
)

from . import utils
