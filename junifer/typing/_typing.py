"""Provide type hints for internal and external use."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from collections.abc import MutableMapping, Sequence
from typing import (
    TYPE_CHECKING,
    Union,
)


if TYPE_CHECKING:
    from ..datagrabber import BaseDataGrabber
    from ..datareader import DefaultDataReader
    from ..markers import BaseMarker
    from ..preprocess import BasePreprocessor
    from ..storage import BaseFeatureStorage


__all__ = [
    "ConditionalDependencies",
    "ConfigVal",
    "DataGrabberLike",
    "DataGrabberPatterns",
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
ConditionalDependencies = Sequence[
    MutableMapping[
        str,
        Union[
            str,
            PipelineComponent,
            Sequence[str],
            Sequence[PipelineComponent],
        ],
    ]
]
ExternalDependencies = Sequence[MutableMapping[str, Union[str, Sequence[str]]]]
MarkerInOutMappings = MutableMapping[str, MutableMapping[str, str]]
DataGrabberPatterns = dict[
    str, Union[dict[str, str], Sequence[dict[str, str]]]
]
ConfigVal = Union[bool, int, float, str]
Element = Union[str, tuple[str, ...]]
Elements = Sequence[Element]
