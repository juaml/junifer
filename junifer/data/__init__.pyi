__all__ = [
    "CoordinatesRegistry",
    "ParcellationRegistry",
    "MaskRegistry",
    "get_template",
    "get_xfm",
    "utils",
]

from .coordinates import CoordinatesRegistry
from .parcellations import ParcellationRegistry
from .masks import MaskRegistry

from .template_spaces import get_template, get_xfm

from . import utils
