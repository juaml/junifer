"""Provide tests for masks."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Vera Komeyer <v.komeyer@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

import pytest
from numpy.testing import assert_array_almost_equal

from junifer.data.masks import (
    _load_vickery_patil_mask,
    list_masks,
    load_mask,
    register_mask,
)


def test_register_mask_built_in_check() -> None:
    """Test mask registration check for built-in masks."""
    with pytest.raises(ValueError, match=r"built-in mask"):
        register_mask(
            name="GM_prob0.2",
            mask_path="testmask.nii.gz",
            overwrite=True,
        )


def test_list_masks_incorrect() -> None:
    """Test incorrect information check for list masks."""
    masks = list_masks()
    assert "testmask" not in masks


def test_register_mask_already_registered() -> None:
    """Test mask registration check for already registered."""
    # Register custom mask
    register_mask(
        name="testmask",
        mask_path="testmask.nii.gz",
    )
    assert load_mask("testmask", path_only=True)[1].name == "testmask.nii.gz"

    # Try registering again
    with pytest.raises(ValueError, match=r"already registered."):
        register_mask(
            name="testmask",
            mask_path="testmask.nii.gz",
        )
    register_mask(
        name="testmask",
        mask_path="testmask2.nii.gz",
        overwrite=True,
    )

    assert load_mask("testmask", path_only=True)[1].name == "testmask2.nii.gz"


@pytest.mark.parametrize(
    "name, mask_path, overwrite",
    [
        ("testmask_1", "testmask_1.nii.gz", True),
        ("testmask_2", "testmask_2.nii.gz", True),
        ("testmask_3", Path("testmask_3.nii.gz"), True),
    ],
)
def test_register_mask(
    name: str,
    mask_path: str,
    overwrite: bool,
) -> None:
    """Test mask registration.

    Parameters
    ----------
    name : str
        The parametrized mask name.
    mask_path : str or pathlib.Path
        The parametrized mask path.
    overwrite : bool
        The parametrized mask overwrite value.

    """
    # Register custom mask
    register_mask(
        name=name,
        mask_path=mask_path,
        overwrite=overwrite,
    )
    # List available mask and check registration
    masks = list_masks()
    assert name in masks
    # Load registered mask
    _, fname = load_mask(name=name, path_only=True)
    # Check values for registered mask
    assert fname.name == f"{name}.nii.gz"


@pytest.mark.parametrize(
    "mask_name",
    [
        "GM_prob0.2",
        "GM_prob0.2_cortex",
    ],
)
def test_list_masks_correct(mask_name: str) -> None:
    """Test correct information check for list masks.

    Parameters
    ----------
    mask_name : str
        The parametrized mask name.

    """
    masks = list_masks()
    assert mask_name in masks


def test_load_mask_incorrect() -> None:
    """Test loading of invalid masks."""
    with pytest.raises(ValueError, match=r"not found"):
        load_mask("wrongmask")


def test_vickery_patil() -> None:
    """Test Vickery-Patil mask."""
    mask, fname = load_mask("GM_prob0.2")
    assert_array_almost_equal(
        mask.header["pixdim"][1:4], [1.5, 1.5, 1.5]  # type: ignore
    )

    assert fname.name == "CAT12_IXI555_MNI152_TMP_GS_GMprob0.2_clean.nii.gz"

    mask, fname = load_mask("GM_prob0.2", resolution=3)
    assert_array_almost_equal(
        mask.header["pixdim"][1:4], [3.0, 3.0, 3.0]  # type: ignore
    )

    assert (
        fname.name == "CAT12_IXI555_MNI152_TMP_GS_GMprob0.2_clean_3mm.nii.gz"
    )

    mask, fname = load_mask("GM_prob0.2_cortex")
    assert_array_almost_equal(
        mask.header["pixdim"][1:4], [3.0, 3.0, 3.0]  # type: ignore
    )

    assert fname.name == "GMprob0.2_cortex_3mm_NA_rm.nii.gz"

    with pytest.raises(ValueError, match=r"find a Vickery-Patil mask "):
        _load_vickery_patil_mask("wrong", resolution=2)
