"""Provide tests for masks."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Vera Komeyer <v.komeyer@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Callable, Dict, Union

from pathlib import Path

import pytest
from numpy.testing import (
    assert_array_almost_equal,
    assert_array_equal,
)

from nilearn.image import resample_to_img
from nilearn.masking import (
    compute_brain_mask,
    compute_background_mask,
    compute_epi_mask,
)
from nilearn.datasets import fetch_icbm152_brain_gm_mask

from junifer.data.masks import (
    _load_vickery_patil_mask,
    list_masks,
    load_mask,
    register_mask,
    get_mask,
    _available_masks,
)

from junifer.datareader import DefaultDataReader
from junifer.testing.datagrabbers import (
    OasisVBMTestingDatagrabber,
    SPMAuditoryTestingDatagrabber,
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


def test_get_mask() -> None:
    """Test the get_mask function."""
    reader = DefaultDataReader()
    with OasisVBMTestingDatagrabber() as dg:
        input = dg["sub-01"]
        input = reader.fit_transform(input)
        vbm_gm = input["VBM_GM"]
        vbm_gm_img = vbm_gm["data"]
        mask = get_mask(mask="GM_prob0.2", target_data=vbm_gm)

        assert mask.shape == vbm_gm_img.shape
        assert_array_equal(mask.affine, vbm_gm_img.affine)

        raw_mask_img, _ = load_mask("GM_prob0.2", resolution=1.5)
        res_mask_img = resample_to_img(
            raw_mask_img,
            vbm_gm_img,
            interpolation="nearest",
            copy=True,
        )
        assert_array_equal(mask.get_fdata(), res_mask_img.get_fdata())


def test_mask_callable() -> None:
    """Test using a callable mask."""

    def ident(x):
        return x

    _available_masks["identity"] = {"family": "Callable", "func": ident}
    reader = DefaultDataReader()
    with OasisVBMTestingDatagrabber() as dg:
        input = dg["sub-01"]
        input = reader.fit_transform(input)
        vbm_gm = input["VBM_GM"]
        vbm_gm_img = vbm_gm["data"]
        mask = get_mask(mask="identity", target_data=vbm_gm)

        assert_array_equal(mask.get_fdata(), vbm_gm_img.get_fdata())

    del _available_masks["identity"]


def test_get_mask_errors() -> None:
    """Test passing wrong parameters to get_mask."""
    reader = DefaultDataReader()
    with OasisVBMTestingDatagrabber() as dg:
        input = dg["sub-01"]
        input = reader.fit_transform(input)
        vbm_gm = input["VBM_GM"]
        with pytest.raises(ValueError, match=r"only one key"):
            get_mask(mask={"GM_prob0.2": {}, "Other": {}}, target_data=vbm_gm)

        with pytest.raises(ValueError, match=r"callable params"):
            get_mask(mask={"GM_prob0.2": {"param": 1}}, target_data=vbm_gm)


@pytest.mark.parametrize(
    "mask_name,function,params,resample",
    [
        ("compute_brain_mask", compute_brain_mask, {"threshold": 0.2}, False),
        ("compute_background_mask", compute_background_mask, None, False),
        ("compute_epi_mask", compute_epi_mask, None, False),
        (
            "fetch_icbm152_brain_gm_mask",
            fetch_icbm152_brain_gm_mask,
            None,
            True,
        ),
    ],
)
def test_nilearn_compute_masks(
    mask_name: str,
    function: Callable,
    params: Union[Dict, None],
    resample: bool,
) -> None:
    """Test using nilearn compute mask functions.

    Parameters
    ----------
    mask_name : str
        Name of the mask.
    function : callable
        Function to call.
    params : dict, optional
        Parameters to pass to the function.
    resample : bool
        Whether to resample the mask to the target data.
    """
    reader = DefaultDataReader()
    with SPMAuditoryTestingDatagrabber() as dg:
        input = dg["sub001"]
        input = reader.fit_transform(input)
        bold = input["BOLD"]
        bold_img = bold["data"]

        if params is None:
            params = {}
            mask_spec = mask_name
        else:
            mask_spec = {mask_name: params}

        mask = get_mask(mask=mask_spec, target_data=bold)

        assert_array_equal(mask.affine, bold_img.affine)

        if resample is False:
            ni_mask = function(bold_img, **params)
        else:
            ni_mask = function(**params)
            # Mask needs resample
            ni_mask = resample_to_img(
                ni_mask,
                bold_img,
                interpolation="nearest",
                copy=True,
            )
        assert_array_equal(mask.get_fdata(), ni_mask.get_fdata())
