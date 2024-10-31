__all__ = [
    "CoordinatesRegistry",
    "ParcellationRegistry",
    "MaskRegistry",
    "get_data",
    "list_data",
    "load_data",
    "register_data",
    "deregister_data",
    "get_template",
    "get_xfm",
    "utils",
]

from .coordinates import CoordinatesRegistry
from .parcellations import ParcellationRegistry
from .masks import MaskRegistry

from ._dispatch import (
    get_data,
    list_data,
    load_data,
    register_data,
    deregister_data,
)

from .template_spaces import get_template, get_xfm

from . import utils
