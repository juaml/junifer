"""Provide type hints for internal and external use."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import sys


if sys.version_info < (3, 12):  # pragma: no cover
    from typing_extensions import TypedDict
else:
    from typing import TypedDict

from collections.abc import Sequence
from typing import (
    TYPE_CHECKING,
    Union,
)


if TYPE_CHECKING:
    from ..data import BasePipelineDataRegistry
    from ..datagrabber import BaseDataGrabber, DataType
    from ..datareader import DefaultDataReader
    from ..markers import BaseMarker
    from ..pipeline import BaseDataDumpAsset, ExtDep
    from ..preprocess import BasePreprocessor
    from ..storage import BaseFeatureStorage, StorageType


__all__ = [
    "ConditionalDependencies",
    "ConfigVal",
    "DataDumpAssetLike",
    "DataGrabberLike",
    "DataGrabberPatterns",
    "DataRegistryLike",
    "Dependencies",
    "Element",
    "Elements",
    "ExternalDependencies",
    "MarkerInOutMappings",
    "MarkerLike",
    "PipelineComponent",
    "PreprocessorLike",
    "StorageLike",
]


class ExternalDependency(TypedDict):
    name: "ExtDep"
    commands: list[str]


class ConditionalDependency(TypedDict):
    using: object
    depends_on: list[object]


DataDumpAssetLike = type["BaseDataDumpAsset"]
DataRegistryLike = type["BasePipelineDataRegistry"]
DataGrabberLike = type["BaseDataGrabber"]
PreprocessorLike = type["BasePreprocessor"]
MarkerLike = type["BaseMarker"]
StorageLike = type["BaseFeatureStorage"]
PipelineComponent = Union[
    "DataGrabberLike",
    "DefaultDataReader",
    "PreprocessorLike",
    "MarkerLike",
    "StorageLike",
]
Dependencies = set[str]
ConditionalDependencies = list[ConditionalDependency]
ExternalDependencies = list[ExternalDependency]
MarkerInOutMappings = dict["DataType", dict[str, "StorageType"]]
DataGrabberPatterns = dict[
    str,
    Union[
        dict[str, Union[str, dict[str, str], list[dict[str, str]]]],
        list[dict[str, str]],
    ],
]

ConfigVal = Union[bool, int, float, str]
Element = Union[str, tuple[str, ...]]
Elements = Sequence[Element]
