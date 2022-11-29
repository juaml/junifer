"""Provide tests for parcellations."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Vera Komeyer <v.komeyer@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import List

import nibabel as nib
import pytest
from nilearn.image import new_img_like
from numpy.testing import assert_array_almost_equal, assert_array_equal

from junifer.data.parcellations import (
    _retrieve_parcellation,
    _retrieve_schaefer,
    _retrieve_suit,
    _retrieve_tian,
    list_parcellations,
    load_parcellation,
    register_parcellation,
)


def test_register_parcellation_built_in_check() -> None:
    """Test parcellation registration check for built-in parcellations."""
    with pytest.raises(ValueError, match=r"built-in parcellation"):
        register_parcellation(
            name="SUITxSUIT",
            parcellation_path="testparc.nii.gz",
            parcels_labels=["1", "2", "3"],
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
        )
    register_parcellation(
        name="testparc",
        parcellation_path="testparc2.nii.gz",
        parcels_labels=["1", "2", "3"],
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
    schaefer, labels, schaefer_path = load_parcellation("Schaefer100x7")
    assert schaefer is not None

    # Test wrong number of labels
    register_parcellation("WrongLabels", schaefer_path, labels[:10])

    with pytest.raises(ValueError, match=r"has 100 parcels but 10"):
        load_parcellation("WrongLabels")

    # Test wrong number of labels
    register_parcellation("WrongLabels2", schaefer_path, labels + ["wrong"])

    with pytest.raises(ValueError, match=r"has 100 parcels but 101"):
        load_parcellation("WrongLabels2")

    schaefer_data = schaefer.get_fdata().copy()
    schaefer_data[schaefer_data == 50] = 0
    new_schaefer_path = tmp_path / "new_schaefer.nii.gz"
    new_schaefer_img = new_img_like(schaefer, schaefer_data)
    nib.save(new_schaefer_img, new_schaefer_path)

    register_parcellation("WrongValues", new_schaefer_path, labels[:-1])
    with pytest.raises(ValueError, match=r"the range [0, 99]"):
        load_parcellation("WrongValues")

    schaefer_data = schaefer.get_fdata().copy()
    schaefer_data[schaefer_data == 50] = 200
    new_schaefer_path = tmp_path / "new_schaefer2.nii.gz"
    new_schaefer_img = new_img_like(schaefer, schaefer_data)
    nib.save(new_schaefer_img, new_schaefer_path)

    register_parcellation("WrongValues2", new_schaefer_path, labels)
    with pytest.raises(ValueError, match=r"the range [0, 100]"):
        load_parcellation("WrongValues2")


@pytest.mark.parametrize(
    "name, parcellation_path, parcels_labels, overwrite",
    [
        ("testparc_1", "testparc_1.nii.gz", ["1", "2", "3"], True),
        ("testparc_2", "testparc_2.nii.gz", ["1", "2", "6"], True),
        ("testparc_3", Path("testparc_3.nii.gz"), ["1", "2", "6"], True),
    ],
)
def test_register_parcellation(
    name: str,
    parcellation_path: str,
    parcels_labels: List[str],
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
    overwrite : bool
        The parametrized parcellation overwrite value.

    """
    # Register custom parcellation
    register_parcellation(
        name=name,
        parcellation_path=parcellation_path,
        parcels_labels=parcels_labels,
        overwrite=overwrite,
    )
    # List available parcellation and check registration
    parcellations = list_parcellations()
    assert name in parcellations
    # Load registered parcellation
    _, lbl, fname = load_parcellation(name=name, path_only=True)
    # Check values for registered parcellation
    assert lbl == parcels_labels
    assert fname.name == f"{name}.nii.gz"


@pytest.mark.parametrize(
    "parcellation_name",
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


# TODO: paramdtrize test
def test_schaefer_parcellation(tmp_path: Path) -> None:
    """Test Schaefer parcellation.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    parcellations = list_parcellations()
    for n_rois in range(100, 1001, 100):
        for t_net in [7, 17]:
            t_name = f"Schaefer{n_rois}x{t_net}"
            assert t_name in parcellations

    # Define parcellation file names
    fname1 = "Schaefer2018_100Parcels_7Networks_order_FSLMNI152_1mm.nii.gz"
    fname2 = "Schaefer2018_100Parcels_7Networks_order_FSLMNI152_2mm.nii.gz"

    # Load parcellation
    img, lbl, fname = load_parcellation(
        name="Schaefer100x7", parcellations_dir=str(tmp_path.absolute())
    )
    # Check parcellation values
    assert img is not None
    assert fname.name == fname1
    assert len(lbl) == 100
    assert_array_equal(img.header["pixdim"][1:4], [1, 1, 1])  # type: ignore

    # Test with Path
    img, lbl, fname = load_parcellation(
        name="Schaefer100x7", parcellations_dir=tmp_path
    )
    # Load parcellation
    img2, lbl, fname = load_parcellation(
        name="Schaefer100x7",
        parcellations_dir=tmp_path,
        resolution=3,
    )
    # Check parcellation values
    assert fname.name == fname2
    assert len(lbl) == 100
    assert img2 is not None
    assert_array_equal(img2.header["pixdim"][1:4], [2, 2, 2])  # type: ignore
    # Load parcellation
    img2, lbl, fname = load_parcellation(
        "Schaefer100x7",
        parcellations_dir=tmp_path,
        resolution=2.1,
    )
    # Check parcellation values
    assert fname.name == fname2
    assert len(lbl) == 100
    assert img2 is not None
    assert_array_equal(img2.header["pixdim"][1:4], [2, 2, 2])  # type: ignore
    # Load parcellation
    img2, lbl, fname = load_parcellation(
        "Schaefer100x7",
        parcellations_dir=tmp_path,
        resolution=1.99,
    )
    # Check parcellation values
    assert fname.name == fname1
    assert len(lbl) == 100
    assert img2 is not None
    assert_array_equal(img2.header["pixdim"][1:4], [1, 1, 1])  # type: ignore
    # Load parcellation
    img2, lbl, fname = load_parcellation(
        "Schaefer100x7",
        parcellations_dir=tmp_path,
        resolution=0.5,
    )
    # Check parcellation values
    assert fname.name == fname1
    assert len(lbl) == 100
    assert img2 is not None
    assert_array_equal(img2.header["pixdim"][1:4], [1, 1, 1])  # type: ignore


def test_load_parcellation_schaefer() -> None:
    """Test Schaefer parcellation loading."""
    img, lbl, fname = load_parcellation(name="Schaefer100x7")
    assert img is not None
    home_dir = Path().home() / "junifer" / "data" / "parcellations"
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
            parcellations_dir=tmp_path,
            resolution=1,
            n_rois=101,
            yeo_networks=7,
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
            parcellations_dir=tmp_path,
            resolution=1,
            n_rois=100,
            yeo_networks=8,
        )


# TODO: parametrize test
def test_suit(tmp_path: Path) -> None:
    """Test SUIT parcellation.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    parcellations = list_parcellations()
    assert "SUITxSUIT" in parcellations
    assert "SUITxMNI" in parcellations

    # Load parcellation
    img, lbl, fname = load_parcellation(
        name="SUITxSUIT", parcellations_dir=tmp_path
    )
    fname1 = "SUIT_SUITSpace_1mm.nii"
    assert img is not None
    assert fname.name == fname1
    assert len(lbl) == 34
    assert_array_equal(img.header["pixdim"][1:4], [1, 1, 1])  # type: ignore

    # Load parcellation
    img, lbl, fname = load_parcellation(
        name="SUITxSUIT", parcellations_dir=tmp_path
    )
    fname1 = "SUIT_SUITSpace_1mm.nii"
    assert img is not None
    assert fname.name == fname1
    assert len(lbl) == 34
    assert_array_equal(img.header["pixdim"][1:4], [1, 1, 1])  # type: ignore

    # Load parcellation
    img, lbl, fname = load_parcellation(
        name="SUITxMNI", parcellations_dir=tmp_path
    )
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
        _retrieve_suit(parcellations_dir=tmp_path, resolution=1, space="wrong")


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
    img, lbl, fname = load_parcellation(
        name=f"TianxS{scale}x3TxMNI6thgeneration",
        parcellations_dir=tmp_path,
    )
    fname1 = f"Tian_Subcortex_S{scale}_3T_1mm.nii.gz"
    assert img is not None
    assert fname.name == fname1
    assert len(lbl) == n_label
    assert_array_equal(img.header["pixdim"][1:4], [1, 1, 1])  # type: ignore
    # Load parcellation
    img, lbl, fname = load_parcellation(
        name=f"TianxS{scale}x3TxMNI6thgeneration",
        parcellations_dir=tmp_path,
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
    img, lbl, fname = load_parcellation(
        name=f"TianxS{scale}x3TxMNInonlinear2009cAsym",
        parcellations_dir=tmp_path,
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
    img, lbl, fname = load_parcellation(
        name=f"TianxS{scale}x7TxMNI6thgeneration", parcellations_dir=tmp_path
    )
    fname1 = f"Tian_Subcortex_S{scale}_7T.nii.gz"
    assert img is not None
    assert fname.name == fname1
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
            parcellations_dir=tmp_path,
            resolution=1,
            scale=1,
            space="wrong",
        )

    with pytest.raises(ValueError, match=r"MNI6thgeneration"):
        _retrieve_tian(
            parcellations_dir=tmp_path,
            resolution=1,
            scale=1,
            magneticfield="7T",
            space="MNInonlinear2009cAsym",
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
            space="MNI6thgeneration",
        )
