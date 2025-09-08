__all__ = [
    "BasePipelineDataRegistry",
    "CoordinatesRegistry",
    "DataDispatcher",
    "ParcellationRegistry",
    "MapsRegistry",
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

from .pipeline_data_registry_base import BasePipelineDataRegistry
from .coordinates import CoordinatesRegistry
from .parcellations import ParcellationRegistry
from .maps import MapsRegistry
from .masks import MaskRegistry

from ._dispatch import (
    DataDispatcher,
    get_data,
    list_data,
    load_data,
    register_data,
    deregister_data,
)

from .template_spaces import get_template, get_xfm

from . import utils
