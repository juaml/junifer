"""Provide tests for parcellations."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Vera Komeyer <v.komeyer@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import List

import nibabel as nib
import numpy as np
import pytest
from nilearn.image import new_img_like, resample_to_img
from numpy.testing import assert_array_almost_equal, assert_array_equal

from junifer.data.parcellations import (
    _retrieve_aicha,
    _retrieve_parcellation,
    _retrieve_schaefer,
    _retrieve_shen,
    _retrieve_suit,
    _retrieve_tian,
    _retrieve_yan,
    get_parcellation,
    list_parcellations,
    load_parcellation,
    merge_parcellations,
    register_parcellation,
)
from junifer.datareader import DefaultDataReader
from junifer.testing.datagrabbers import OasisVBMTestingDataGrabber


def test_register_parcellation_built_in_check() -> None:
    """Test parcellation registration check for built-in parcellations."""
    with pytest.raises(ValueError, match=r"built-in parcellation"):
        register_parcellation(
            name="SUITxSUIT",
            parcellation_path="testparc.nii.gz",
            parcels_labels=["1", "2", "3"],
            space="SUIT",
            overwrite=True,
        )


def test_list_parcellations_incorrect() -> None:
    """Test incorrect information check for list parcellations."""
    parcellations = list_parcellations()
    assert "testparc" not in parcellations


def test_register_parcellation_already_registered() -> None:
    """Test parcellation registration check for already registered."""
    # Register custom parcellation
    register_parcellation(
        name="testparc",
        parcellation_path="testparc.nii.gz",
        parcels_labels=["1", "2", "3"],
        space="MNI",
    )
    assert (
        load_parcellation("testparc", path_only=True)[2].name
        == "testparc.nii.gz"
    )

    # Try registering again
    with pytest.raises(ValueError, match=r"already registered."):
        register_parcellation(
            name="testparc",
            parcellation_path="testparc.nii.gz",
            parcels_labels=["1", "2", "3"],
            space="MNI",
        )
    register_parcellation(
        name="testparc",
        parcellation_path="testparc2.nii.gz",
        parcels_labels=["1", "2", "3"],
        space="MNI",
        overwrite=True,
    )

    assert (
        load_parcellation("testparc", path_only=True)[2].name
        == "testparc2.nii.gz"
    )


def test_parcellation_wrong_labels_values(tmp_path: Path) -> None:
    """Test parcellation with wrong labels and values.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    schaefer, labels, schaefer_path, _ = load_parcellation("Schaefer100x7")
    assert schaefer is not None

    # Test wrong number of labels
    register_parcellation("WrongLabels", schaefer_path, labels[:10], "MNI")

    with pytest.raises(ValueError, match=r"has 100 parcels but 10"):
        load_parcellation("WrongLabels")

    # Test wrong number of labels
    register_parcellation(
        "WrongLabels2", schaefer_path, [*labels, "wrong"], "MNI"
    )

    with pytest.raises(ValueError, match=r"has 100 parcels but 101"):
        load_parcellation("WrongLabels2")

    schaefer_data = schaefer.get_fdata().copy()
    schaefer_data[schaefer_data == 50] = 0
    new_schaefer_path = tmp_path / "new_schaefer.nii.gz"
    new_schaefer_img = new_img_like(schaefer, schaefer_data)
    nib.save(new_schaefer_img, new_schaefer_path)

    register_parcellation("WrongValues", new_schaefer_path, labels[:-1], "MNI")
    with pytest.raises(ValueError, match=r"the range [0, 99]"):
        load_parcellation("WrongValues")

    schaefer_data = schaefer.get_fdata().copy()
    schaefer_data[schaefer_data == 50] = 200
    new_schaefer_path = tmp_path / "new_schaefer2.nii.gz"
    new_schaefer_img = new_img_like(schaefer, schaefer_data)
    nib.save(new_schaefer_img, new_schaefer_path)

    register_parcellation("WrongValues2", new_schaefer_path, labels, "MNI")
    with pytest.raises(ValueError, match=r"the range [0, 100]"):
        load_parcellation("WrongValues2")


@pytest.mark.parametrize(
    "name, parcellation_path, parcels_labels, space, overwrite",
    [
        ("testparc_1", "testparc_1.nii.gz", ["1", "2", "3"], "MNI", True),
        ("testparc_2", "testparc_2.nii.gz", ["1", "2", "6"], "MNI", True),
        (
            "testparc_3",
            Path("testparc_3.nii.gz"),
            ["1", "2", "6"],
            "MNI",
            True,
        ),
    ],
)
def test_register_parcellation(
    name: str,
    parcellation_path: str,
    parcels_labels: List[str],
    space: str,
    overwrite: bool,
) -> None:
    """Test parcellation registration.

    Parameters
    ----------
    name : str
        The parametrized parcellation name.
    parcellation_path : str or pathlib.Path
        The parametrized parcellation path.
    parcels_labels : list of str
        The parametrized parcellation labels.
    space : str
        The parametrized parcellation space.
    overwrite : bool
        The parametrized parcellation overwrite value.

    """
    # Register custom parcellation
    register_parcellation(
        name=name,
        parcellation_path=parcellation_path,
        parcels_labels=parcels_labels,
        space=space,
        overwrite=overwrite,
    )
    # List available parcellation and check registration
    parcellations = list_parcellations()
    assert name in parcellations
    # Load registered parcellation
    _, lbl, fname, parcellation_space = load_parcellation(
        name=name, path_only=True
    )
    # Check values for registered parcellation
    assert lbl == parcels_labels
    assert fname.name == f"{name}.nii.gz"
    assert parcellation_space == space


@pytest.mark.parametrize(
    "parcellation_name",
    [
        "AICHA_v1",
        "AICHA_v2",
        "SUITxSUIT",
        "SUITxMNI",
        "Schaefer100x7",
        "Schaefer100x17",
        "TianxS1x7TxMNI6thgeneration",
        "TianxS3x3TxMNI6thgeneration",
        "TianxS4x3TxMNInonlinear2009cAsym",
    ],
)
def test_list_parcellations_correct(parcellation_name: str) -> None:
    """Test correct information check for list parcellations.

    Parameters
    ----------
    parcellation_name : str
        The parametrized parcellation name.

    """
    parcellations = list_parcellations()
    assert parcellation_name in parcellations


def test_load_parcellation_incorrect() -> None:
    """Test loading of invalid parcellations."""
    with pytest.raises(ValueError, match=r"not found"):
        load_parcellation("wrongparcellation")


def test_retrieve_parcellation_incorrect() -> None:
    """Test retrieval of invalid parcellations."""
    with pytest.raises(ValueError, match=r"provided parcellation name"):
        _retrieve_parcellation("wrongparcellation")


@pytest.mark.parametrize(
    "resolution, n_rois, yeo_networks",
    [
        (1.0, 100, 7),
        (1.0, 200, 7),
        (1.0, 300, 7),
        (1.0, 400, 7),
        (1.0, 500, 7),
        (1.0, 600, 7),
        (1.0, 700, 7),
        (1.0, 800, 7),
        (1.0, 900, 7),
        (1.0, 1000, 7),
        (2.0, 100, 7),
        (2.0, 200, 7),
        (2.0, 300, 7),
        (2.0, 400, 7),
        (2.0, 500, 7),
        (2.0, 600, 7),
        (2.0, 700, 7),
        (2.0, 800, 7),
        (2.0, 900, 7),
        (2.0, 1000, 7),
        (1.0, 100, 17),
        (1.0, 200, 17),
        (1.0, 300, 17),
        (1.0, 400, 17),
        (1.0, 500, 17),
        (1.0, 600, 17),
        (1.0, 700, 17),
        (1.0, 800, 17),
        (1.0, 900, 17),
        (1.0, 1000, 17),
        (2.0, 100, 17),
        (2.0, 200, 17),
        (2.0, 300, 17),
        (2.0, 400, 17),
        (2.0, 500, 17),
        (2.0, 600, 17),
        (2.0, 700, 17),
        (2.0, 800, 17),
        (2.0, 900, 17),
        (2.0, 1000, 17),
    ],
)
def test_schaefer(
    tmp_path: Path,
    resolution: float,
    n_rois: int,
    yeo_networks: int,
) -> None:
    """Test Schaefer parcellation.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    resolution : float
        The parametrized resolution values.
    n_rois : int
        The parametrized ROI count values.
    yeo_networks : int
        The parametrized Yeo networks values.

    """
    parcellations = list_parcellations()
    parcellation_name = f"Schaefer{n_rois}x{yeo_networks}"
    assert parcellation_name in parcellations

    parcellation_file = (
        f"Schaefer2018_{n_rois}Parcels_{yeo_networks}Networks_order_FSLMNI152_"
        f"{int(resolution)}mm.nii.gz"
    )
    # Load parcellation
    img, label, img_path, space = load_parcellation(
        name=parcellation_name,
        parcellations_dir=tmp_path,
        resolution=resolution,
    )
    assert img is not None
    assert img_path.name == parcellation_file
    assert len(label) == n_rois
    assert space == "MNI152NLin6Asym"
    assert_array_equal(
        img.header["pixdim"][1:4], 3 * [resolution]  # type: ignore
    )


def test_retrieve_schaefer_incorrect_n_rois(tmp_path: Path) -> None:
    """Test retrieve Schaefer with incorrect ROIs.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with pytest.raises(ValueError, match=r"The parameter `n_rois`"):
        _retrieve_schaefer(
            parcellations_dir=tmp_path,
            resolution=1,
            n_rois=101,
            yeo_networks=7,
        )


def test_retrieve_schaefer_incorrect_yeo_networks(tmp_path: Path) -> None:
    """Test retrieve Schaefer with incorrect Yeo networks.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with pytest.raises(ValueError, match=r"The parameter `yeo_networks`"):
        _retrieve_schaefer(
            parcellations_dir=tmp_path,
            resolution=1,
            n_rois=100,
            yeo_networks=8,
        )


@pytest.mark.parametrize(
    "space_key, space",
    [("SUIT", "SUIT"), ("MNI", "MNI152NLin6Asym")],
)
def test_suit(tmp_path: Path, space_key: str, space: str) -> None:
    """Test SUIT parcellation.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    space_key : str
        The parametrized space values for the key.
    space : str
        The parametrized space values.

    """
    parcellations = list_parcellations()
    assert f"SUITx{space_key}" in parcellations
    # Load parcellation
    img, label, img_path, parcellation_space = load_parcellation(
        name=f"SUITx{space_key}",
        parcellations_dir=tmp_path,
    )
    assert img is not None
    assert img_path.name == f"SUIT_{space_key}Space_1mm.nii"
    assert parcellation_space == space
    assert len(label) == 34
    assert_array_equal(img.header["pixdim"][1:4], [1, 1, 1])  # type: ignore


def test_retrieve_suit_incorrect_space(tmp_path: Path) -> None:
    """Test retrieve SUIT with incorrect space.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with pytest.raises(ValueError, match=r"The parameter `space`"):
        _retrieve_suit(
            parcellations_dir=tmp_path, resolution=1.0, space="wrong"
        )


@pytest.mark.parametrize(
    "scale, n_label", [(1, 16), (2, 32), (3, 50), (4, 54)]
)
def test_tian_3T_6thgeneration(
    tmp_path: Path, scale: int, n_label: int
) -> None:
    """Test Tian parcellation.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    scale : int
        The parametrized scale values.
    n_label : int
        The parametrized n_label values.

    """
    parcellations = list_parcellations()
    assert "TianxS1x3TxMNI6thgeneration" in parcellations
    assert "TianxS2x3TxMNI6thgeneration" in parcellations
    assert "TianxS3x3TxMNI6thgeneration" in parcellations
    assert "TianxS4x3TxMNI6thgeneration" in parcellations
    # Load parcellation
    img, lbl, fname, parcellation_space_1 = load_parcellation(
        name=f"TianxS{scale}x3TxMNI6thgeneration", parcellations_dir=tmp_path
    )
    fname1 = f"Tian_Subcortex_S{scale}_3T_1mm.nii.gz"
    assert img is not None
    assert fname.name == fname1
    assert parcellation_space_1 == "MNI152NLin6Asym"
    assert len(lbl) == n_label
    assert_array_equal(img.header["pixdim"][1:4], [1, 1, 1])  # type: ignore
    # Load parcellation
    img, lbl, fname, parcellation_space_2 = load_parcellation(
        name=f"TianxS{scale}x3TxMNI6thgeneration",
        parcellations_dir=tmp_path,
        resolution=2,
    )
    fname1 = f"Tian_Subcortex_S{scale}_3T.nii.gz"
    assert img is not None
    assert fname.name == fname1
    assert parcellation_space_2 == "MNI152NLin6Asym"
    assert len(lbl) == n_label
    assert_array_equal(img.header["pixdim"][1:4], [2, 2, 2])  # type: ignore


@pytest.mark.parametrize(
    "scale, n_label", [(1, 16), (2, 32), (3, 50), (4, 54)]
)
def test_tian_3T_nonlinear2009cAsym(
    tmp_path: Path, scale: int, n_label: int
) -> None:
    """Test Tian parcellation.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    scale : int
        The parametrized scale values.
    n_label : int
        The parametrized n_label values.

    """
    parcellations = list_parcellations()
    assert "TianxS1x3TxMNInonlinear2009cAsym" in parcellations
    assert "TianxS2x3TxMNInonlinear2009cAsym" in parcellations
    assert "TianxS3x3TxMNInonlinear2009cAsym" in parcellations
    assert "TianxS4x3TxMNInonlinear2009cAsym" in parcellations
    # Load parcellation
    img, lbl, fname, space = load_parcellation(
        name=f"TianxS{scale}x3TxMNInonlinear2009cAsym",
        parcellations_dir=tmp_path,
    )
    fname1 = f"Tian_Subcortex_S{scale}_3T_2009cAsym.nii.gz"
    assert img is not None
    assert fname.name == fname1
    assert space == "MNI152NLin2009cAsym"
    assert len(lbl) == n_label
    assert_array_equal(img.header["pixdim"][1:4], [2, 2, 2])  # type: ignore


@pytest.mark.parametrize(
    "scale, n_label", [(1, 16), (2, 34), (3, 54), (4, 62)]
)
def test_tian_7T_6thgeneration(
    tmp_path: Path, scale: int, n_label: int
) -> None:
    """Test Tian parcellation.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    scale : int
        The parametrized scale values.
    n_label : int
        The parametrized n_label values.

    """
    parcellations = list_parcellations()
    assert "TianxS1x7TxMNI6thgeneration" in parcellations
    assert "TianxS2x7TxMNI6thgeneration" in parcellations
    assert "TianxS3x7TxMNI6thgeneration" in parcellations
    assert "TianxS4x7TxMNI6thgeneration" in parcellations
    # Load parcellation
    img, lbl, fname, space = load_parcellation(
        name=f"TianxS{scale}x7TxMNI6thgeneration", parcellations_dir=tmp_path
    )
    fname1 = f"Tian_Subcortex_S{scale}_7T.nii.gz"
    assert img is not None
    assert fname.name == fname1
    assert space == "MNI152NLin6Asym"
    assert len(lbl) == n_label
    assert_array_almost_equal(
        img.header["pixdim"][1:4], [1.6, 1.6, 1.6]  # type: ignore
    )


def test_retrieve_tian_incorrect_space(tmp_path: Path) -> None:
    """Test retrieve tian with incorrect space.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with pytest.raises(ValueError, match=r"The parameter `space`"):
        _retrieve_tian(
            parcellations_dir=tmp_path, resolution=1, scale=1, space="wrong"
        )

    with pytest.raises(ValueError, match=r"MNI152NLin6Asym"):
        _retrieve_tian(
            parcellations_dir=tmp_path,
            resolution=1,
            scale=1,
            magneticfield="7T",
            space="MNI152NLin2009cAsym",
        )


def test_retrieve_tian_incorrect_magneticfield(tmp_path: Path) -> None:
    """Test retrieve tian with incorrect magneticfield.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with pytest.raises(ValueError, match=r"The parameter `magneticfield`"):
        _retrieve_tian(
            parcellations_dir=tmp_path,
            resolution=1,
            scale=1,
            magneticfield="wrong",
        )


def test_retrieve_tian_incorrect_scale(tmp_path: Path) -> None:
    """Test retrieve tian with incorrect scale.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with pytest.raises(ValueError, match=r"The parameter `scale`"):
        _retrieve_tian(
            parcellations_dir=tmp_path,
            resolution=1,
            scale=5,
            space="MNI152NLin6Asym",
        )


@pytest.mark.parametrize("version", [1, 2])
def test_aicha(tmp_path: Path, version: int) -> None:
    """Test AICHA parcellation.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    version : int
        The parametrized version values.

    """
    parcellations = list_parcellations()
    assert f"AICHA_v{version}" in parcellations
    # Load parcellation
    img, label, img_path, space = load_parcellation(
        name=f"AICHA_v{version}", parcellations_dir=tmp_path
    )
    assert img is not None
    assert img_path.name == "AICHA.nii"
    assert space == "IXI549Space"
    assert len(label) == 384
    assert_array_equal(img.header["pixdim"][1:4], [2, 2, 2])  # type: ignore


def test_retrieve_aicha_incorrect_version(tmp_path: Path) -> None:
    """Test retrieve AICHA with incorrect version.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with pytest.raises(ValueError, match="The parameter `version`"):
        _retrieve_aicha(
            parcellations_dir=tmp_path,
            version=100,
        )


@pytest.mark.parametrize(
    "resolution, year, n_rois, n_labels, img_name",
    [
        (1.0, 2013, 50, 93, "fconn_atlas"),
        (1.0, 2013, 50, 93, "fconn_atlas"),
        (1.0, 2013, 100, 184, "fconn_atlas"),
        (1.0, 2013, 100, 184, "fconn_atlas"),
        (1.0, 2013, 150, 278, "fconn_atlas"),
        (1.0, 2013, 150, 278, "fconn_atlas"),
        (1.0, 2015, 268, 268, "268_parcellation"),
        (1.0, 2015, 268, 268, "268_parcellation"),
        (1.0, 2019, 368, 368, "368_parcellation"),
    ],
)
def test_shen(
    tmp_path: Path,
    resolution: float,
    year: int,
    n_rois: int,
    n_labels: int,
    img_name: str,
) -> None:
    """Test Shen parcellation.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    resolution : float
        The parametrized resolution values.
    year : int
        The parametrized year values.
    n_rois : int
        The parametrized ROI count values.
    n_labels : int
        The parametrized label count values.
    img_name : str
        The parametrized partial file names.

    """
    parcellations = list_parcellations()
    assert f"Shen_{year}_{n_rois}" in parcellations
    # Load parcellation
    img, label, img_path, space = load_parcellation(
        name=f"Shen_{year}_{n_rois}",
        parcellations_dir=tmp_path,
        resolution=resolution,
    )
    assert img is not None
    assert img_name in img_path.name
    assert space == "MNI152NLin2009cAsym"
    assert len(label) == n_labels
    assert_array_equal(
        img.header["pixdim"][1:4], 3 * [resolution]  # type: ignore
    )


def test_retrieve_shen_incorrect_year(tmp_path: Path) -> None:
    """Test retrieve Shen with incorrect year.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with pytest.raises(ValueError, match="The parameter `year`"):
        _retrieve_shen(
            parcellations_dir=tmp_path,
            year=1969,
        )


def test_retrieve_shen_incorrect_n_rois(tmp_path: Path) -> None:
    """Test retrieve Shen with incorrect ROIs.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with pytest.raises(ValueError, match="The parameter `n_rois`"):
        _retrieve_shen(
            parcellations_dir=tmp_path,
            year=2015,
            n_rois=10,
        )


@pytest.mark.parametrize(
    "resolution, year, n_rois",
    [
        (2.0, 2019, 368),
        (1.0, 2013, 268),
        (1.0, 2013, 368),
        (1.0, 2015, 50),
        (1.0, 2015, 100),
        (1.0, 2015, 150),
        (1.0, 2019, 50),
        (1.0, 2019, 100),
        (1.0, 2019, 150),
        (1.0, 2015, 368),
        (1.0, 2019, 268),
    ],
)
def test_retrieve_shen_incorrect_param_combo(
    tmp_path: Path,
    resolution: float,
    year: int,
    n_rois: int,
) -> None:
    """Test retrieve Shen with incorrect parameter combinations.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    resolution : float
        The parametrized resolution values.
    year : int
        The parametrized year values.
    n_rois : int
        The parametrized ROI count values.

    """
    with pytest.raises(ValueError, match="The parameter combination"):
        _retrieve_shen(
            parcellations_dir=tmp_path,
            resolution=resolution,
            year=year,
            n_rois=n_rois,
        )


@pytest.mark.parametrize(
    "resolution, n_rois, yeo_networks, kong_networks",
    [
        (1.0, 100, 7, None),
        (1.0, 200, 7, None),
        (1.0, 300, 7, None),
        (1.0, 400, 7, None),
        (1.0, 500, 7, None),
        (1.0, 600, 7, None),
        (1.0, 700, 7, None),
        (1.0, 800, 7, None),
        (1.0, 900, 7, None),
        (1.0, 1000, 7, None),
        (2.0, 100, 7, None),
        (2.0, 200, 7, None),
        (2.0, 300, 7, None),
        (2.0, 400, 7, None),
        (2.0, 500, 7, None),
        (2.0, 600, 7, None),
        (2.0, 700, 7, None),
        (2.0, 800, 7, None),
        (2.0, 900, 7, None),
        (2.0, 1000, 7, None),
        (1.0, 100, 17, None),
        (1.0, 200, 17, None),
        (1.0, 300, 17, None),
        (1.0, 400, 17, None),
        (1.0, 500, 17, None),
        (1.0, 600, 17, None),
        (1.0, 700, 17, None),
        (1.0, 800, 17, None),
        (1.0, 900, 17, None),
        (1.0, 1000, 17, None),
        (2.0, 100, 17, None),
        (2.0, 200, 17, None),
        (2.0, 300, 17, None),
        (2.0, 400, 17, None),
        (2.0, 500, 17, None),
        (2.0, 600, 17, None),
        (2.0, 700, 17, None),
        (2.0, 800, 17, None),
        (2.0, 900, 17, None),
        (2.0, 1000, 17, None),
        (1.0, 100, None, 17),
        (1.0, 200, None, 17),
        (1.0, 300, None, 17),
        (1.0, 400, None, 17),
        (1.0, 500, None, 17),
        (1.0, 600, None, 17),
        (1.0, 700, None, 17),
        (1.0, 800, None, 17),
        (1.0, 900, None, 17),
        (1.0, 1000, None, 17),
        (2.0, 100, None, 17),
        (2.0, 200, None, 17),
        (2.0, 300, None, 17),
        (2.0, 400, None, 17),
        (2.0, 500, None, 17),
        (2.0, 600, None, 17),
        (2.0, 700, None, 17),
        (2.0, 800, None, 17),
        (2.0, 900, None, 17),
        (2.0, 1000, None, 17),
    ],
)
def test_yan(
    tmp_path: Path,
    resolution: float,
    n_rois: int,
    yeo_networks: int,
    kong_networks: int,
) -> None:
    """Test Yan parcellation.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    resolution : float
        The parametrized resolution values.
    n_rois : int
        The parametrized ROI count values.
    yeo_networks : int
        The parametrized Yeo networks values.
    kong_networks : int
        The parametrized Kong networks values.

    """
    parcellations = list_parcellations()
    if yeo_networks:
        parcellation_name = f"Yan{n_rois}xYeo{yeo_networks}"
        assert parcellation_name in parcellations
        parcellation_file = (
            f"{n_rois}Parcels_Yeo2011_{yeo_networks}Networks_FSLMNI152_"
            f"{int(resolution)}mm.nii.gz"
        )
    elif kong_networks:
        parcellation_name = f"Yan{n_rois}xKong{kong_networks}"
        assert parcellation_name in parcellations
        parcellation_file = (
            f"{n_rois}Parcels_Kong2022_{kong_networks}Networks_FSLMNI152_"
            f"{int(resolution)}mm.nii.gz"
        )
    # Load parcellation
    img, label, img_path, space = load_parcellation(
        name=parcellation_name,  # type: ignore
        parcellations_dir=tmp_path,
        resolution=resolution,
    )
    assert img is not None
    assert img_path.name == parcellation_file  # type: ignore
    assert space == "MNI152NLin6Asym"
    assert len(label) == n_rois
    assert_array_equal(
        img.header["pixdim"][1:4], 3 * [resolution]  # type: ignore
    )


def test_retrieve_yan_incorrect_networks(tmp_path: Path) -> None:
    """Test retrieve Yan with incorrect networks.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with pytest.raises(
        ValueError, match="Either one of `yeo_networks` or `kong_networks`"
    ):
        _retrieve_yan(
            parcellations_dir=tmp_path,
            n_rois=31418,
            yeo_networks=100,
            kong_networks=100,
        )

    with pytest.raises(
        ValueError, match="Either one of `yeo_networks` or `kong_networks`"
    ):
        _retrieve_yan(
            parcellations_dir=tmp_path,
            n_rois=31418,
            yeo_networks=None,
            kong_networks=None,
        )


def test_retrieve_yan_incorrect_n_rois(tmp_path: Path) -> None:
    """Test retrieve Yan with incorrect ROIs.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with pytest.raises(ValueError, match="The parameter `n_rois`"):
        _retrieve_yan(
            parcellations_dir=tmp_path,
            n_rois=31418,
            yeo_networks=7,
        )


def test_retrieve_yan_incorrect_yeo_networks(tmp_path: Path) -> None:
    """Test retrieve Yan with incorrect Yeo networks.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with pytest.raises(ValueError, match="The parameter `yeo_networks`"):
        _retrieve_yan(
            parcellations_dir=tmp_path,
            n_rois=100,
            yeo_networks=27,
        )


def test_retrieve_yan_incorrect_kong_networks(tmp_path: Path) -> None:
    """Test retrieve Yan with incorrect Kong networks.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with pytest.raises(ValueError, match="The parameter `kong_networks`"):
        _retrieve_yan(
            parcellations_dir=tmp_path,
            n_rois=100,
            kong_networks=27,
        )


def test_merge_parcellations() -> None:
    """Test merging parcellations."""
    # load some parcellations for testing
    schaefer_parcellation, schaefer_labels, _, _ = load_parcellation(
        "Schaefer100x17"
    )
    tian_parcellation, tian_labels, _, _ = load_parcellation(
        "TianxS2x3TxMNInonlinear2009cAsym"
    )
    # prepare the list of the actual parcellations
    parcellation_list = [schaefer_parcellation, tian_parcellation]
    # prepare a list of names
    names = ["Schaefer100x17", "TianxS2x3TxMNInonlinear2009cAsym"]
    # prepare a list of label lists
    labels_lists = [schaefer_labels, tian_labels]
    # merge the parcellations
    merged_parc, labels = merge_parcellations(
        parcellation_list, names, labels_lists
    )

    # we should have 132 integer labels plus 1 for background
    parc_data = merged_parc.get_fdata()
    assert len(np.unique(parc_data)) == 133
    # no background label, so labels is one less
    assert len(labels) == 132


def test_merge_parcellations_3D_multiple_non_overlapping(
    tmp_path: Path,
) -> None:
    """Test merge_parcellations with multiple non-overlapping parcellations.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    # Get the testing parcellation
    parcellation, labels, _, _ = load_parcellation("Schaefer100x7")

    assert parcellation is not None

    # Create two parcellations from it
    parcellation_data = parcellation.get_fdata()
    parcellation1_data = parcellation_data.copy()
    parcellation1_data[parcellation1_data > 50] = 0
    parcellation2_data = parcellation_data.copy()
    parcellation2_data[parcellation2_data <= 50] = 0
    parcellation2_data[parcellation2_data > 0] -= 50
    labels1 = labels[:50]
    labels2 = labels[50:]

    parcellation1_img = new_img_like(parcellation, parcellation1_data)
    parcellation2_img = new_img_like(parcellation, parcellation2_data)

    parcellation_list = [parcellation1_img, parcellation2_img]
    names = ["high", "low"]
    labels_lists = [labels1, labels2]

    merged_parc, _ = merge_parcellations(
        parcellation_list, names, labels_lists
    )

    parc_data = parcellation.get_fdata()
    assert_array_equal(parc_data, merged_parc.get_fdata())
    assert len(labels) == 100
    assert len(np.unique(parc_data)) == 101  # 100 + 1 because background 0


def test_merge_parcellations_3D_multiple_overlapping() -> None:
    """Test merge_parcellations with multiple overlapping parcellations."""

    # Get the testing parcellation
    parcellation, labels, _, _ = load_parcellation("Schaefer100x7")

    assert parcellation is not None

    # Create two parcellations from it
    parcellation_data = parcellation.get_fdata()
    parcellation1_data = parcellation_data.copy()
    parcellation1_data[parcellation1_data > 50] = 0
    parcellation2_data = parcellation_data.copy()

    # Make the second parcellation overlap with the first
    parcellation2_data[parcellation2_data <= 45] = 0
    parcellation2_data[parcellation2_data > 0] -= 45
    labels1 = [f"low_{x}" for x in labels[:50]]  # Change the labels
    labels2 = [f"high_{x}" for x in labels[45:]]  # Change the labels

    parcellation1_img = new_img_like(parcellation, parcellation1_data)
    parcellation2_img = new_img_like(parcellation, parcellation2_data)

    parcellation_list = [parcellation1_img, parcellation2_img]
    names = ["high", "low"]
    labels_lists = [labels1, labels2]

    with pytest.warns(RuntimeWarning, match="overlapping voxels"):
        merged_parc, merged_labels = merge_parcellations(
            parcellation_list, names, labels_lists
        )

    parc_data = parcellation.get_fdata()
    assert len(labels) == 100
    assert len(np.unique(parc_data)) == 101  # 100 + 1 because background 0


def test_merge_parcellations_3D_multiple_duplicated_labels() -> None:
    """Test merge_parcellations with duplicated labels."""

    # Get the testing parcellation
    parcellation, labels, _, _ = load_parcellation("Schaefer100x7")

    assert parcellation is not None

    # Create two parcellations from it
    parcellation_data = parcellation.get_fdata()
    parcellation1_data = parcellation_data.copy()
    parcellation1_data[parcellation1_data > 50] = 0
    parcellation2_data = parcellation_data.copy()
    parcellation2_data[parcellation2_data <= 50] = 0
    parcellation2_data[parcellation2_data > 0] -= 50
    labels1 = labels[:50]
    labels2 = labels[49:-1]  # One label is duplicated

    parcellation1_img = new_img_like(parcellation, parcellation1_data)
    parcellation2_img = new_img_like(parcellation, parcellation2_data)

    parcellation_list = [parcellation1_img, parcellation2_img]
    names = ["high", "low"]
    labels_lists = [labels1, labels2]

    with pytest.warns(RuntimeWarning, match="duplicated labels."):
        merged_parc, merged_labels = merge_parcellations(
            parcellation_list, names, labels_lists
        )

    parc_data = parcellation.get_fdata()
    assert_array_equal(parc_data, merged_parc.get_fdata())
    assert len(labels) == 100
    assert len(np.unique(parc_data)) == 101  # 100 + 1 because background 0


def test_get_parcellation_single() -> None:
    """Test tailored single parcellation fetch."""
    reader = DefaultDataReader()
    with OasisVBMTestingDataGrabber() as dg:
        element = dg["sub-01"]
        element_data = reader.fit_transform(element)
        vbm_gm = element_data["VBM_GM"]
        vbm_gm_img = vbm_gm["data"]
        # Get tailored parcellation
        tailored_parcellation, tailored_labels = get_parcellation(
            parcellation=["Schaefer100x7"],
            target_data=vbm_gm,
        )
        # Check shape and affine with original element data
        assert tailored_parcellation.shape == vbm_gm_img.shape
        assert_array_equal(tailored_parcellation.affine, vbm_gm_img.affine)
        # Get raw parcellation
        raw_parcellation, raw_labels, _, _ = load_parcellation(
            "Schaefer100x7",
            resolution=1.5,
        )
        resampled_raw_parcellation = resample_to_img(
            source_img=raw_parcellation,
            target_img=vbm_gm_img,
            interpolation="nearest",
            copy=True,
        )
        # Check resampled data with tailored data
        assert_array_equal(
            tailored_parcellation.get_fdata(),
            resampled_raw_parcellation.get_fdata(),
        )
        assert tailored_labels == raw_labels


def test_get_parcellation_multi_same_space() -> None:
    """Test tailored multi parcellation fetch in same space."""
    reader = DefaultDataReader()
    with OasisVBMTestingDataGrabber() as dg:
        element = dg["sub-01"]
        element_data = reader.fit_transform(element)
        vbm_gm = element_data["VBM_GM"]
        vbm_gm_img = vbm_gm["data"]
        # Get tailored parcellation
        tailored_parcellation, tailored_labels = get_parcellation(
            parcellation=[
                "Schaefer100x7",
                "TianxS2x3TxMNI6thgeneration",
            ],
            target_data=vbm_gm,
        )
        # Check shape and affine with original element data
        assert tailored_parcellation.shape == vbm_gm_img.shape
        assert_array_equal(tailored_parcellation.affine, vbm_gm_img.affine)
        # Get raw parcellations
        raw_parcellations = []
        raw_labels = []
        parcellations_names = [
            "Schaefer100x7",
            "TianxS2x3TxMNI6thgeneration",
        ]
        for name in parcellations_names:
            img, labels, _, _ = load_parcellation(name=name, resolution=1.5)
            # Resample raw parcellations
            resampled_img = resample_to_img(
                source_img=img,
                target_img=vbm_gm_img,
                interpolation="nearest",
                copy=True,
            )
            raw_parcellations.append(resampled_img)
            raw_labels.append(labels)
        # Merge resampled parcellations
        merged_resampled_parcellations, merged_labels = merge_parcellations(
            parcellations_list=raw_parcellations,
            parcellations_names=parcellations_names,
            labels_lists=raw_labels,
        )
        # Check resampled data with tailored data
        assert_array_equal(
            tailored_parcellation.get_fdata(),
            merged_resampled_parcellations.get_fdata(),
        )
        assert tailored_labels == merged_labels


def test_get_parcellation_multi_different_space() -> None:
    """Test tailored multi parcellation fetch in different space."""
    reader = DefaultDataReader()
    with OasisVBMTestingDataGrabber() as dg:
        element = dg["sub-01"]
        element_data = reader.fit_transform(element)
        vbm_gm = element_data["VBM_GM"]
        # Get tailored parcellation
        with pytest.raises(RuntimeError, match="unable to merge."):
            get_parcellation(
                parcellation=[
                    "Schaefer100x7",
                    "SUITxSUIT",
                ],
                target_data=vbm_gm,
            )
