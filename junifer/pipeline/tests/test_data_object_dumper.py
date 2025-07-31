"""Provide tests for data object dumping."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import pickle
from pathlib import Path
from typing import Union

import nibabel
import pytest

from junifer.markers import FunctionalConnectivitySpheres
from junifer.pipeline import (
    AssetDumperDispatcher,
    AssetLoaderDispatcher,
    BaseDataDumpAsset,
    DataObjectDumper,
    MarkerCollection,
)
from junifer.preprocess import fMRIPrepConfoundRemover
from junifer.testing.datagrabbers import PartlyCloudyTestingDataGrabber
from junifer.utils import config


@pytest.mark.parametrize(
    "dispatcher, inbuilt_key, ext_key, val",
    [
        (
            AssetDumperDispatcher,
            nibabel.Nifti1Image,
            nibabel.Nifti2Image,
            dict,
        ),
        (AssetLoaderDispatcher, ".nii", ".tsv", dict),
    ],
)
def test_dispatcher_addition_errors(
    dispatcher: Union[AssetDumperDispatcher, AssetLoaderDispatcher],
    inbuilt_key: Union[str, type],
    ext_key: Union[str, type],
    val: type,
) -> None:
    """Test asset dumper / loader addition errors.

    Parameters
    ----------
    dispatcher : AssetDumperDispatcher or AssetLoaderDispatcher,
        The parametrized dispatcher.
    inbuilt_key : str or type
        The parametrized in-built key.
    ext_key : str or type
        The parametrized external key.
    val : type
        The parametrized value.

    """
    with pytest.raises(ValueError, match="Cannot set"):
        dispatcher()[inbuilt_key] = val

    with pytest.raises(ValueError, match="Invalid"):
        dispatcher()[ext_key] = val


@pytest.mark.parametrize(
    "dispatcher, inbuilt_key, ext_key",
    [
        (AssetDumperDispatcher, nibabel.Nifti1Image, nibabel.Nifti2Image),
        (AssetLoaderDispatcher, ".nii", ".tsv"),
    ],
)
def test_dispatcher_removal_errors(
    dispatcher: Union[AssetDumperDispatcher, AssetLoaderDispatcher],
    inbuilt_key: Union[str, type],
    ext_key: Union[str, type],
) -> None:
    """Test asset dumper / loader removal errors.

    Parameters
    ----------
    dispatcher : AssetDumperDispatcher or AssetLoaderDispatcher,
        The parametrized dispatcher.
    inbuilt_key : str or type
        The parametrized in-built key.
    ext_key : str or type
        The parametrized external key.

    """
    with pytest.raises(ValueError, match="Cannot delete"):
        _ = dispatcher().pop(inbuilt_key)

    with pytest.raises(KeyError, match=f"{ext_key}"):
        del dispatcher()[ext_key]


def test_dispatcher() -> None:
    """Test asset dumper / loader addition and removal."""

    class Int(int): ...

    class Float(float): ...

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

    AssetDumperDispatcher().update({nibabel.Nifti2Image: DumAsset})
    assert nibabel.Nifti2Image in AssetDumperDispatcher()
    _ = AssetDumperDispatcher().pop(nibabel.Nifti2Image)
    assert nibabel.Nifti2Image not in AssetDumperDispatcher()

    AssetLoaderDispatcher().update({".n+2": DumAsset})
    assert ".n+2" in AssetLoaderDispatcher()
    _ = AssetLoaderDispatcher().pop(".n+2")
    assert ".n+2" not in AssetLoaderDispatcher()


@pytest.mark.parametrize(
    "granularity, expected_dir_count",
    [
        ("full", 2),
        ("final", 1),
    ],
)
def test_data_object_dumper(
    tmp_path: Path, granularity: str, expected_dir_count: int
) -> None:
    """Test data object dumper.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    granularity : str
        The parametrized granularity.
    expected_dir_count : int
        The parametrized expected directory count.

    """
    config.set(key="preprocessing.dump.location", val=tmp_path)
    config.set(key="preprocessing.dump.granularity", val=granularity)

    mc = MarkerCollection(
        preprocessors=[
            fMRIPrepConfoundRemover(
                strategy={
                    "motion": "full",
                    "wm_csf": "full",
                },
                detrend=True,
                standardize=True,
                low_pass=0.08,
                high_pass=0.01,
            ),
        ],
        markers=[
            FunctionalConnectivitySpheres(
                name="dmnbuckner_5mm_fc_spheres",
                coords="DMNBuckner",
                radius=5.0,
                conn_method="correlation",
            ),
        ],
    )
    dg = PartlyCloudyTestingDataGrabber()

    with dg:
        mc.fit(dg["sub-01"])

    dirs = list(tmp_path.iterdir())
    assert len(dirs) == expected_dir_count

    dump_load = DataObjectDumper().load(dirs[-1] / "data.yaml")
    assert "BOLD" in dump_load

    config.delete("preprocessing.dump.location")
    config.delete("preprocessing.dump.granularity")


def test_data_object_dumper_with_warp(tmp_path: Path) -> None:
    """Test data object dumper with Warp data type.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    DataObjectDumper().dump(
        data={
            "Warp": [
                {
                    "path": (
                        tmp_path / "from-MNI152NLin2009cAsym_to-T1w_"
                        "mode-image_xfm.h5"
                    ),
                    "src": "MNI152NLin2009cAsym",
                    "dst": "native",
                    "warper": "ants",
                },
                {
                    "path": (
                        tmp_path / "from-T1w_to-MNI152NLin2009cAsym_"
                        "mode-image_xfm.h5"
                    ),
                    "src": "native",
                    "dst": "MNI152NLin2009cAsym",
                    "warper": "ants",
                },
            ],
        },
        path=tmp_path,
        step="warp_test",
    )
    dump_load = DataObjectDumper().load(tmp_path / "warp_test" / "data.yaml")
    assert "Warp" in dump_load
