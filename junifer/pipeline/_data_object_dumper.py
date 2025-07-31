"""Provide pipeline data object dumper and data dump asset classes."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from abc import ABC, abstractmethod
from collections.abc import Iterator, MutableMapping
from copy import deepcopy
from pathlib import Path
from typing import Any

import nibabel
import pandas

from ..utils import raise_error, yaml


__all__ = [
    "AssetDumperDispatcher",
    "AssetLoaderDispatcher",
    "BaseDataDumpAsset",
    "DataObjectDumper",
]


class BaseDataDumpAsset(ABC):
    """Abstract base class for a data dump asset.

    Parameters
    ----------
    data : Any
        Data to save.
    path_without_ext : pathlib.Path
        Path to the asset without extension.
        The subclass should add the extension when saving.

    """

    def __init__(self, data: Any, path_without_ext: Path) -> None:
        """Initialize the class."""
        self.data = data
        self.path_without_ext = path_without_ext

    @abstractmethod
    def dump(self) -> None:
        """Dump asset."""
        raise_error(
            msg="Concrete classes need to implement dump().",
            klass=NotImplementedError,
        )

    @classmethod
    @abstractmethod
    def load(cls: type["BaseDataDumpAsset"], path: Path) -> Any:
        """Load asset from path."""
        raise_error(
            msg="Concrete classes need to implement load().",
            klass=NotImplementedError,
        )


class Nifti1ImageAsset(BaseDataDumpAsset):
    """Class for ``nibabel.Nifti1Image`` dumper."""

    def dump(self) -> None:
        nibabel.save(self.data, self.path_without_ext.with_suffix(".nii.gz"))

    @classmethod
    def load(cls: "Nifti1ImageAsset", path: Path) -> nibabel.Nifti1Image:
        return nibabel.load(path)


class PandasDataFrameAsset(BaseDataDumpAsset):
    """Class for ``pandas.DataFrame`` dumper."""

    def dump(self) -> None:
        self.data.to_csv(self.path_without_ext.with_suffix(".csv"))

    @classmethod
    def load(cls: "PandasDataFrameAsset", path: Path) -> pandas.DataFrame:
        return pandas.read_csv(path, index_col=0)


class AssetDumperDispatcher(MutableMapping):
    """Class for helping dynamic asset dumper dispatch."""

    _instance = None

    def __new__(cls):
        # Make class singleton
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Set dumpers
            cls._dumpers: dict[type, type[BaseDataDumpAsset]] = {}
            cls._builtin: dict[type, type[BaseDataDumpAsset]] = {}
            cls._external: dict[type, type[BaseDataDumpAsset]] = {}
            cls._builtin.update(
                {
                    nibabel.Nifti1Image: Nifti1ImageAsset,
                    pandas.DataFrame: PandasDataFrameAsset,
                }
            )
            cls._dumpers.update(cls._builtin)
        return cls._instance

    def __getitem__(self, key: type) -> type[BaseDataDumpAsset]:
        return self._dumpers[key]

    def __iter__(self) -> Iterator[type]:
        return iter(self._dumpers)

    def __len__(self) -> int:
        return len(self._dumpers)

    def __delitem__(self, key: type) -> None:
        # Internal check
        if key in self._builtin:
            raise_error(f"Cannot delete in-built key: {key}")
        # Non-existing key
        if key not in self._external:
            raise_error(klass=KeyError, msg=str(key))
        # Update external
        _ = self._external.pop(key)
        # Update global
        _ = self._dumpers.pop(key)

    def __setitem__(self, key: type, value: type[BaseDataDumpAsset]) -> None:
        # Internal check
        if key in self._builtin:
            raise_error(f"Cannot set value for in-built key: {key}")
        # Value type check
        if not issubclass(value, BaseDataDumpAsset):
            raise_error(f"Invalid value type: {type(value)}")
        # Update external
        self._external[key] = value
        # Update global
        self._dumpers[key] = value

    def popitem():
        """Not implemented."""
        pass

    def clear(self):
        """Not implemented."""
        pass

    def setdefault(self, key: type, value=None):
        """Not implemented."""
        pass


class AssetLoaderDispatcher(MutableMapping):
    """Class for helping dynamic asset loader dispatch."""

    _instance = None

    def __new__(cls):
        # Make class singleton
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Set loaders
            cls._loaders: dict[str, type[BaseDataDumpAsset]] = {}
            cls._builtin: dict[str, type[BaseDataDumpAsset]] = {}
            cls._external: dict[str, type[BaseDataDumpAsset]] = {}
            cls._builtin.update(
                {
                    ".nii.gz": Nifti1ImageAsset,
                    ".nii": Nifti1ImageAsset,
                    ".csv": PandasDataFrameAsset,
                }
            )
            cls._loaders.update(cls._builtin)
        return cls._instance

    def __getitem__(self, key: str) -> type[BaseDataDumpAsset]:
        return self._loaders[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._loaders)

    def __len__(self) -> int:
        return len(self._loaders)

    def __delitem__(self, key: str) -> None:
        # Internal check
        if key in self._builtin:
            raise_error(f"Cannot delete in-built key: {key}")
        # Non-existing key
        if key not in self._external:
            raise_error(klass=KeyError, msg=key)
        # Update external
        _ = self._external.pop(key)
        # Update global
        _ = self._loaders.pop(key)

    def __setitem__(self, key: str, value: type[BaseDataDumpAsset]) -> None:
        # Internal check
        if key in self._builtin:
            raise_error(f"Cannot set value for in-built key: {key}")
        # Value type check
        if not issubclass(value, BaseDataDumpAsset):
            raise_error(f"Invalid value type: {type(value)}")
        # Update external
        self._external[key] = value
        # Update global
        self._loaders[key] = value

    def popitem():
        """Not implemented."""
        pass

    def clear(self):
        """Not implemented."""
        pass

    def setdefault(self, key: str, value=None):
        """Not implemented."""
        pass


class DataObjectDumper:
    """Class for pipeline data object dumping."""

    _instance = None

    def __new__(cls):
        """Overridden to make the class singleton."""
        # Make class singleton
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def dump(self, data: dict, path: Path, step: str) -> None:
        """Dump data object at path.

        Parameters
        ----------
        data : dict
            The data object state to dump.
        path : pathlib.Path
            The path to dump the data object.
        step : str
            The step name. Also sets the dump directory.

        """
        # Make a deep copy of data
        data_copy = deepcopy(data)
        # Initialize list for storing assets to save
        assets = []

        dump_file_root = path / step

        for k, v in data_copy.items():
            # Conditional for Warp type; kept separate for low cognitive load
            if isinstance(v, list):
                for idx, _ in enumerate(v):
                    data_copy[k][idx]["path"] = str(data_copy[k][idx]["path"])
                continue

            # Transform Path to str
            data_copy[k]["path"] = str(data_copy[k]["path"])
            # Pop out first level assets; some data types might not have
            if "data" in v:
                dumper = AssetDumperDispatcher()[type(v["data"])]
                assets.append(
                    dumper(
                        data=v.pop("data"),
                        path_without_ext=dump_file_root / k,
                    )
                )
            for kk, vv in v.items():
                if isinstance(vv, dict) and kk != "meta":
                    # Transform Path to str
                    data_copy[k][kk]["path"] = str(data_copy[k][kk]["path"])
                    # Pop out second level assets
                    if "data" in vv:
                        dumper = AssetDumperDispatcher()[type(vv["data"])]
                        assets.append(
                            dumper(
                                data=vv.pop("data"),
                                path_without_ext=dump_file_root / f"{k}_{kk}",
                            )
                        )

        # Save yaml
        dump_file_path = dump_file_root / "data.yaml"
        dump_file_path.parent.mkdir(parents=True, exist_ok=True)
        yaml.dump(data_copy, stream=dump_file_path)

        # Save assets
        for x in assets:
            x.dump()

    def load(self, path: Path) -> dict:
        """Load data object from path.

        Parameters
        ----------
        path : pathlib.Path
            The path to the dumped data object.

        Returns
        -------
        dict
            The restored data object dump.

        """
        data = yaml.load(path)
        # Load assets; stem => path mapping
        assets = {
            child.stem.split(".")[0]: child
            for child in path.parent.iterdir()
            if "".join(child.suffixes) in AssetLoaderDispatcher()
        }

        for k, v in data.items():
            # Conditional for Warp type; kept separate for low cognitive load
            if isinstance(v, list):
                for idx, _ in enumerate(v):
                    data[k][idx]["path"] = Path(data[k][idx]["path"])
                continue

            # Transform str to Path
            data[k]["path"] = Path(data[k]["path"])
            # Insert first level assets if matching asset is found
            if k in assets:
                # Get path
                p = assets[k]
                data[k]["path"] = p
                # Get correct loader using extension
                loader = AssetLoaderDispatcher()["".join(p.suffixes)]
                data[k]["data"] = loader.load(p)
            for kk, vv in v.items():
                if isinstance(vv, dict) and kk != "meta":
                    # Transform str to Path
                    data[k][kk]["path"] = Path(data[k][kk]["path"])
                    # Insert second level assets
                    key = f"{k}_{kk}"
                    if key in assets:
                        # Get path
                        pp = assets[key]
                        data[k][kk]["path"] = pp
                        # Get correct loader using extension
                        loader = AssetLoaderDispatcher()["".join(pp.suffixes)]
                        data[k][kk]["data"] = loader.load(pp)

        return data
