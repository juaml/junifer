"""Provide tests for public decorators."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import pickle

from junifer.api.decorators import (
    register_data_dump_asset,
    register_data_registry,
)
from junifer.data import BasePipelineDataRegistry, DataDispatcher
from junifer.pipeline import (
    AssetDumperDispatcher,
    AssetLoaderDispatcher,
    BaseDataDumpAsset,
)


def test_register_data_registry() -> None:
    """Test data registry registration."""

    @register_data_registry("dumb")
    class DumDum(BasePipelineDataRegistry):
        def __init__(self):
            super().__init__()

        def register(self):
            pass

        def deregister(self):
            pass

        def load(self):
            pass

        def get(self):
            pass

    assert "dumb" in DataDispatcher()
    _ = DataDispatcher().pop("dumb")
    assert "dumb" not in DataDispatcher()


def test_register_data_dump_asset() -> None:
    """Test data dump asset registration."""

    class Int(int): ...

    class Float(float): ...

    @register_data_dump_asset([Int, Float], [".int", ".float"])
    class DumAsset(BaseDataDumpAsset):
        def dump(self):
            suffix = ""
            if isinstance(self.data, Int):
                suffix = ".int"
            else:
                suffix = ".float"
            pickle.dump(self.data, self.path_without_ext.with_suffix(suffix))

        @classmethod
        def load(cls, path):
            return pickle.load(path)

    assert Int in AssetDumperDispatcher()
    assert Float in AssetDumperDispatcher()
    _ = AssetDumperDispatcher().pop(Int)
    _ = AssetDumperDispatcher().pop(Float)
    assert Int not in AssetDumperDispatcher()
    assert Float not in AssetDumperDispatcher()

    assert ".int" in AssetLoaderDispatcher()
    assert ".float" in AssetLoaderDispatcher()
    _ = AssetLoaderDispatcher().pop(".int")
    _ = AssetLoaderDispatcher().pop(".float")
    assert ".int" not in AssetLoaderDispatcher()
    assert ".float" not in AssetLoaderDispatcher()
