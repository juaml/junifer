"""Provide imports for data sub-package."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from .atlases import list_atlases, register_atlas, load_atlas
from .coordinates import (
    list_coordinates,
    register_coordinates,
    load_coordinates,
)
