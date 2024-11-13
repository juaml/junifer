"""Provide type hints for internal and external use."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import (
    TYPE_CHECKING,
    AbstractSet,
    MutableMapping,
    Sequence,
    Type,
    Union,
)


if TYPE_CHECKING:
    from ..datagrabber import BaseDataGrabber
    from ..datareader import DefaultDataReader
    from ..markers import BaseMarker
    from ..preprocess import BasePreprocessor
    from ..storage import BaseFeatureStorage


__all__ = [
    "DataGrabberLike",
    "PreprocessorLike",
    "MarkerLike",
    "StorageLike",
    "PipelineComponent",
    "Dependencies",
    "ConditionalDependencies",
    "ExternalDependencies",
    "MarkerInOutMappings",
]


DataGrabberLike = Type["BaseDataGrabber"]
PreprocessorLike = Type["BasePreprocessor"]
MarkerLike = Type["BaseMarker"]
StorageLike = Type["BaseFeatureStorage"]
PipelineComponent = Union[
    "DataGrabberLike",
    "DefaultDataReader",
    "PreprocessorLike",
    "MarkerLike",
    "StorageLike",
]
Dependencies = AbstractSet[str]
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
