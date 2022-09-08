"""Provide tests for atlas."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Vera Komeyer <v.komeyer@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import List

import pytest
from numpy.testing import assert_array_almost_equal, assert_array_equal

from junifer.data.atlases import (
    _retrieve_atlas,
    _retrieve_schaefer,
    _retrieve_suit,
    _retrieve_tian,
    list_atlases,
    load_atlas,
    register_atlas,
)


def test_register_atlas_built_in_check() -> None:
    """Test atlas registration check for built-in atlas."""
    with pytest.raises(ValueError, match=r"built-in atlas"):
        register_atlas(
            name="SUITxSUIT",
            atlas_path="testatlas.nii.gz",
            atl_labels=["1", "2", "3"],
            overwrite=True,
        )


def test_list_atlases_incorrect() -> None:
    """Test incorrect information check for list atlases."""
    atlases = list_atlases()
    assert "testatlas" not in atlases


def test_register_atlas_already_registered() -> None:
    """Test atlas registration check for already registered atlas."""
    # Register custom atlas
    register_atlas(
        name="testatlas",
        atlas_path="testatlas.nii.gz",
        atl_labels=["1", "2", "3"],
    )
    # Try registering again
    with pytest.raises(ValueError, match=r"already registered."):
        register_atlas(
            name="testatlas",
            atlas_path="testatlas.nii.gz",
            atl_labels=["1", "2", "3"],
        )


@pytest.mark.parametrize(
    "name, atlas_path, atlas_labels, overwrite",
    [
        ("testatlas_1", "testatlas_1.nii.gz", ["1", "2", "3"], True),
        ("testatlas_2", "testatlas_2.nii.gz", ["1", "2", "6"], True),
        ("testatlas_3", Path("testatlas_3.nii.gz"), ["1", "2", "6"], True),
    ],
)
def test_register_atlas(
    name: str,
    atlas_path: str,
    atlas_labels: List[str],
    overwrite: bool,
) -> None:
    """Test atlas registration.

    Parameters
    ----------
    name : str
        The parametrized atlas name.
    atlas_path : str or pathlib.Path
        The parametrized atlas path.
    atlas_labels : list of str
        The parametrized atlas labels.
    overwrite : bool
        The parametrized atlas overwrite value.

    """
    # Register custom atlas
    register_atlas(
        name=name,
        atlas_path=atlas_path,
        atl_labels=atlas_labels,
        overwrite=overwrite,
    )
    # List available atlas and check registration
    atlases = list_atlases()
    assert name in atlases
    # Load registered atlas
    _, lbl, fname = load_atlas(name=name, path_only=True)
    # Check values for registered atlas
    assert lbl == atlas_labels
    assert fname.name == f"{name}.nii.gz"


@pytest.mark.parametrize(
    "atlas_name",
    [
        "SUITxSUIT",
        "SUITxMNI",
        "Schaefer100x7",
        "Schaefer100x17",
        "TianxS1x7TxMNI6thgeneration",
        "TianxS3x3TxMNI6thgeneration",
        "TianxS4x3TxMNInonlinear2009cAsym",
    ],
)
def test_list_atlases_correct(atlas_name: str) -> None:
    """Test correct information check for list atlases.

    Parameters
    ----------
    atlas_name : str
        The parametrized atlas name.

    """
    atlases = list_atlases()
    assert atlas_name in atlases


def test_load_atlas_incorrect() -> None:
    """Test loading of invalid atlas."""
    with pytest.raises(ValueError, match=r"not found"):
        load_atlas("wrongatlas")


def test_retrieve_atlas_incorrect() -> None:
    """Test retrieval of invalid atlas."""
    with pytest.raises(ValueError, match=r"provided atlas name"):
        _retrieve_atlas("wrongatlas")


# TODO: paramdtrize test
def test_schaefer_atlas(tmp_path: Path) -> None:
    """Test Schaefer atlas.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    atlases = list_atlases()
    for n_rois in range(100, 1001, 100):
        for t_net in [7, 17]:
            t_name = f"Schaefer{n_rois}x{t_net}"
            assert t_name in atlases

    # Define atlas file names
    fname1 = "Schaefer2018_100Parcels_7Networks_order_FSLMNI152_1mm.nii.gz"
    fname2 = "Schaefer2018_100Parcels_7Networks_order_FSLMNI152_2mm.nii.gz"

    # Load atlas
    img, lbl, fname = load_atlas(
        name="Schaefer100x7", atlas_dir=str(tmp_path.absolute())
    )
    # Check atlas values
    assert img is not None
    assert fname.name == fname1
    assert len(lbl) == 100
    assert_array_equal(img.header["pixdim"][1:4], [1, 1, 1])  # type: ignore

    # Test with Path
    img, lbl, fname = load_atlas(name="Schaefer100x7", atlas_dir=tmp_path)
    # Load atlas
    img2, lbl, fname = load_atlas(
        name="Schaefer100x7",
        atlas_dir=tmp_path,
        resolution=3,
    )
    # Check atlas values
    assert fname.name == fname2
    assert len(lbl) == 100
    assert img2 is not None
    assert_array_equal(img2.header["pixdim"][1:4], [2, 2, 2])  # type: ignore
    # Load atlas
    img2, lbl, fname = load_atlas(
        "Schaefer100x7",
        atlas_dir=tmp_path,
        resolution=2.1,
    )
    # Check atlas values
    assert fname.name == fname2
    assert len(lbl) == 100
    assert img2 is not None
    assert_array_equal(img2.header["pixdim"][1:4], [2, 2, 2])  # type: ignore
    # Load atlas
    img2, lbl, fname = load_atlas(
        "Schaefer100x7",
        atlas_dir=tmp_path,
        resolution=1.99,
    )
    # Check atlas values
    assert fname.name == fname1
    assert len(lbl) == 100
    assert img2 is not None
    assert_array_equal(img2.header["pixdim"][1:4], [1, 1, 1])  # type: ignore
    # Load atlas
    img2, lbl, fname = load_atlas(
        "Schaefer100x7",
        atlas_dir=tmp_path,
        resolution=0.5,
    )
    # Check atlas values
    assert fname.name == fname1
    assert len(lbl) == 100
    assert img2 is not None
    assert_array_equal(img2.header["pixdim"][1:4], [1, 1, 1])  # type: ignore


def test_load_atlas_schaefer() -> None:
    """Test Schaefer atlas loading."""
    img, lbl, fname = load_atlas(name="Schaefer100x7")
    assert img is not None
    home_dir = Path().home() / "junifer" / "data" / "atlas"
    assert home_dir in fname.parents


def test_retrieve_schaefer_incorrect_n_rois(tmp_path: Path) -> None:
    """Test retrieve schaefer with incorrect n_rois.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with pytest.raises(ValueError, match=r"The parameter `n_rois`"):
        _retrieve_schaefer(
            atlas_dir=tmp_path, resolution=1, n_rois=101, yeo_networks=7
        )


def test_retrieve_schaefer_incorrect_yeo_networks(tmp_path: Path) -> None:
    """Test retrieve schaefer with incorrect yeo_networks.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with pytest.raises(ValueError, match=r"The parameter `yeo_networks`"):
        _retrieve_schaefer(
            atlas_dir=tmp_path, resolution=1, n_rois=100, yeo_networks=8
        )


# TODO: parametrize test
def test_suit(tmp_path: Path) -> None:
    """Test SUIT atlas.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    atlases = list_atlases()
    assert "SUITxSUIT" in atlases
    assert "SUITxMNI" in atlases

    # Load atlas
    img, lbl, fname = load_atlas(name="SUITxSUIT", atlas_dir=tmp_path)
    fname1 = "SUIT_SUITSpace_1mm.nii"
    assert img is not None
    assert fname.name == fname1
    assert len(lbl) == 34
    assert_array_equal(img.header["pixdim"][1:4], [1, 1, 1])  # type: ignore

    # Load atlas
    img, lbl, fname = load_atlas(name="SUITxSUIT", atlas_dir=tmp_path)
    fname1 = "SUIT_SUITSpace_1mm.nii"
    assert img is not None
    assert fname.name == fname1
    assert len(lbl) == 34
    assert_array_equal(img.header["pixdim"][1:4], [1, 1, 1])  # type: ignore

    # Load atlas
    img, lbl, fname = load_atlas(name="SUITxMNI", atlas_dir=tmp_path)
    fname1 = "SUIT_MNISpace_1mm.nii"
    assert img is not None
    assert fname.name == fname1
    assert len(lbl) == 34
    assert_array_equal(img.header["pixdim"][1:4], [1, 1, 1])  # type: ignore


def test_retrieve_suit_incorrect_space(tmp_path: Path) -> None:
    """Test retrieve suit with incorrect space.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with pytest.raises(ValueError, match=r"The parameter `space`"):
        _retrieve_suit(atlas_dir=tmp_path, resolution=1, space="wrong")


@pytest.mark.parametrize(
    "scale, n_label",
    [
        (1, 16),
        (2, 32),
        (3, 50),
        (4, 54),
    ],
)
def test_tian_3T_6thgeneration(
    tmp_path: Path,
    scale: int,
    n_label: int,
) -> None:
    """Test Tian atlas.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    scale : int
        The parametrized scale values.
    n_label : int
        The parametrized n_label values.

    """
    atlases = list_atlases()
    assert "TianxS1x3TxMNI6thgeneration" in atlases
    assert "TianxS2x3TxMNI6thgeneration" in atlases
    assert "TianxS3x3TxMNI6thgeneration" in atlases
    assert "TianxS4x3TxMNI6thgeneration" in atlases
    # Load atlas
    img, lbl, fname = load_atlas(
        name=f"TianxS{scale}x3TxMNI6thgeneration",
        atlas_dir=tmp_path,
    )
    fname1 = f"Tian_Subcortex_S{scale}_3T_1mm.nii.gz"
    assert img is not None
    assert fname.name == fname1
    assert len(lbl) == n_label
    assert_array_equal(img.header["pixdim"][1:4], [1, 1, 1])  # type: ignore
    # Load atlas
    img, lbl, fname = load_atlas(
        name=f"TianxS{scale}x3TxMNI6thgeneration",
        atlas_dir=tmp_path,
        resolution=2,
    )
    fname1 = f"Tian_Subcortex_S{scale}_3T.nii.gz"
    assert img is not None
    assert fname.name == fname1
    assert len(lbl) == n_label
    assert_array_equal(img.header["pixdim"][1:4], [2, 2, 2])  # type: ignore


@pytest.mark.parametrize(
    "scale, n_label",
    [
        (1, 16),
        (2, 32),
        (3, 50),
        (4, 54),
    ],
)
def test_tian_3T_nonlinear2009cAsym(
    tmp_path: Path,
    scale: int,
    n_label: int,
) -> None:
    """Test Tian atlas.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    scale : int
        The parametrized scale values.
    n_label : int
        The parametrized n_label values.

    """
    atlases = list_atlases()
    assert "TianxS1x3TxMNInonlinear2009cAsym" in atlases
    assert "TianxS2x3TxMNInonlinear2009cAsym" in atlases
    assert "TianxS3x3TxMNInonlinear2009cAsym" in atlases
    assert "TianxS4x3TxMNInonlinear2009cAsym" in atlases
    # Load atlas
    img, lbl, fname = load_atlas(
        name=f"TianxS{scale}x3TxMNInonlinear2009cAsym",
        atlas_dir=tmp_path,
    )
    fname1 = f"Tian_Subcortex_S{scale}_3T_2009cAsym.nii.gz"
    assert img is not None
    assert fname.name == fname1
    assert len(lbl) == n_label
    assert_array_equal(img.header["pixdim"][1:4], [2, 2, 2])  # type: ignore


@pytest.mark.parametrize(
    "scale, n_label",
    [
        (1, 16),
        (2, 34),
        (3, 54),
        (4, 62),
    ],
)
def test_tian_7T_6thgeneration(
    tmp_path: Path,
    scale: int,
    n_label: int,
) -> None:
    """Test Tian atlas.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    scale : int
        The parametrized scale values.
    n_label : int
        The parametrized n_label values.

    """
    atlases = list_atlases()
    assert "TianxS1x7TxMNI6thgeneration" in atlases
    assert "TianxS2x7TxMNI6thgeneration" in atlases
    assert "TianxS3x7TxMNI6thgeneration" in atlases
    assert "TianxS4x7TxMNI6thgeneration" in atlases
    # Load atlas
    img, lbl, fname = load_atlas(
        name=f"TianxS{scale}x7TxMNI6thgeneration", atlas_dir=tmp_path
    )
    fname1 = f"Tian_Subcortex_S{scale}_7T.nii.gz"
    assert img is not None
    assert fname.name == fname1
    assert len(lbl) == n_label
    assert_array_almost_equal(
        img.header["pixdim"][1:4], [1.6, 1.6, 1.6])  # type: ignore


def test_retrieve_tian_incorrect_space(tmp_path: Path) -> None:
    """Test retrieve tian with incorrect space.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with pytest.raises(ValueError, match=r"The parameter `space`"):
        _retrieve_tian(
            atlas_dir=tmp_path,
            resolution=1,
            scale=1,
            space="wrong",
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
            atlas_dir=tmp_path,
            resolution=1,
            scale=1,
            magneticfield="wrong",
        )
