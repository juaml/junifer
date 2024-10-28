__all__ = [
    "list_parcellations",
    "load_parcellation",
    "register_parcellation",
    "merge_parcellations",
    "get_parcellation",
    "CoordinatesRegistry",
    "MaskRegistry",
    "get_template",
    "get_xfm",
    "utils",
]

from .parcellations import (
    list_parcellations,
    load_parcellation,
    register_parcellation,
    merge_parcellations,
    get_parcellation,
)
from .coordinates import CoordinatesRegistry
from .masks import MaskRegistry

from .template_spaces import get_template, get_xfm

from . import utils
