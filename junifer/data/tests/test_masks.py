"""Provide tests for masks."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Vera Komeyer <v.komeyer@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import Callable, Dict, List, Optional, Union

import numpy as np
import pytest
from nilearn.datasets import fetch_icbm152_brain_gm_mask
from nilearn.image import resample_to_img
from nilearn.masking import (
    compute_background_mask,
    compute_brain_mask,
    compute_epi_mask,
    intersect_masks,
)
from numpy.testing import assert_array_almost_equal, assert_array_equal

from junifer.data.masks import (
    _available_masks,
    _load_vickery_patil_mask,
    get_mask,
    list_masks,
    load_mask,
    register_mask,
)
from junifer.datareader import DefaultDataReader
from junifer.testing.datagrabbers import (
    OasisVBMTestingDataGrabber,
    SPMAuditoryTestingDataGrabber,
)


def test_register_mask_built_in_check() -> None:
    """Test mask registration check for built-in masks."""
    with pytest.raises(ValueError, match=r"built-in mask"):
        register_mask(
            name="GM_prob0.2",
            mask_path="testmask.nii.gz",
            space="MNI",
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
        space="MNI",
    )
    out = load_mask("testmask", path_only=True)
    assert out[1] is not None
    assert out[1].name == "testmask.nii.gz"

    # Try registering again
    with pytest.raises(ValueError, match=r"already registered."):
        register_mask(
            name="testmask",
            mask_path="testmask.nii.gz",
            space="MNI",
        )
    register_mask(
        name="testmask",
        mask_path="testmask2.nii.gz",
        space="MNI",
        overwrite=True,
    )

    out = load_mask("testmask", path_only=True)
    assert out[1] is not None
    assert out[1].name == "testmask2.nii.gz"


@pytest.mark.parametrize(
    "name, mask_path, space, overwrite",
    [
        ("testmask_1", "testmask_1.nii.gz", "MNI", True),
        ("testmask_2", "testmask_2.nii.gz", "MNI", True),
        ("testmask_3", Path("testmask_3.nii.gz"), "MNI", True),
    ],
)
def test_register_mask(
    name: str,
    mask_path: str,
    space: str,
    overwrite: bool,
) -> None:
    """Test mask registration.

    Parameters
    ----------
    name : str
        The parametrized mask name.
    mask_path : str or pathlib.Path
        The parametrized mask path.
    space : str
        The parametrized mask space.
    overwrite : bool
        The parametrized mask overwrite value.

    """
    # Register custom mask
    register_mask(
        name=name,
        mask_path=mask_path,
        space=space,
        overwrite=overwrite,
    )
    # List available mask and check registration
    masks = list_masks()
    assert name in masks
    # Load registered mask
    _, fname, mask_space = load_mask(name=name, path_only=True)
    # Check values for registered mask
    assert fname is not None
    assert fname.name == f"{name}.nii.gz"
    assert space == mask_space


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


@pytest.mark.parametrize(
    "name, resolution, pixdim, fname",
    [
        (
            "GM_prob0.2",
            None,
            [1.5, 1.5, 1.5],
            "CAT12_IXI555_MNI152_TMP_GS_GMprob0.2_clean.nii.gz",
        ),
        (
            "GM_prob0.2",
            3.0,
            [3.0, 3.0, 3.0],
            "CAT12_IXI555_MNI152_TMP_GS_GMprob0.2_clean_3mm.nii.gz",
        ),
        (
            "GM_prob0.2_cortex",
            None,
            [3.0, 3.0, 3.0],
            "GMprob0.2_cortex_3mm_NA_rm.nii.gz",
        ),
    ],
)
def test_vickery_patil(
    name: str,
    resolution: Optional[float],
    pixdim: List[float],
    fname: str,
) -> None:
    """Test Vickery-Patil mask.

    Parameters
    ----------
    name : str
        The parametrized name of the mask.
    resolution : float or None
        The parametrized resolution of the mask.
    pixdim : list of float
        The parametrized pixel dimensions of the mask.
    fname : str
        The parametrized name of the mask file.

    """
    mask, mask_fname, space = load_mask(name, resolution=resolution)
    assert_array_almost_equal(
        mask.header["pixdim"][1:4], pixdim  # type: ignore
    )
    assert space == "IXI549Space"
    assert mask_fname is not None
    assert mask_fname.name == fname


def test_vickery_patil_error() -> None:
    """Test error for Vickery-Patil mask."""
    with pytest.raises(ValueError, match=r"find a Vickery-Patil mask "):
        _load_vickery_patil_mask(name="wrong", resolution=2.0)


def test_get_mask() -> None:
    """Test the get_mask function."""
    reader = DefaultDataReader()
    with OasisVBMTestingDataGrabber() as dg:
        input = dg["sub-01"]
        input = reader.fit_transform(input)
        vbm_gm = input["VBM_GM"]
        vbm_gm_img = vbm_gm["data"]
        mask = get_mask(masks="GM_prob0.2", target_data=vbm_gm)

        assert mask.shape == vbm_gm_img.shape
        assert_array_equal(mask.affine, vbm_gm_img.affine)

        raw_mask_img, _, _ = load_mask("GM_prob0.2", resolution=1.5)
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

    _available_masks["identity"] = {
        "family": "Callable",
        "func": ident,
        "space": "MNI",
    }
    reader = DefaultDataReader()
    with OasisVBMTestingDataGrabber() as dg:
        input = dg["sub-01"]
        input = reader.fit_transform(input)
        vbm_gm = input["VBM_GM"]
        vbm_gm_img = vbm_gm["data"]
        mask = get_mask(masks="identity", target_data=vbm_gm)

        assert_array_equal(mask.get_fdata(), vbm_gm_img.get_fdata())

    del _available_masks["identity"]


def test_get_mask_errors() -> None:
    """Test passing wrong parameters to get_mask."""
    reader = DefaultDataReader()
    with OasisVBMTestingDataGrabber() as dg:
        input = dg["sub-01"]
        input = reader.fit_transform(input)
        vbm_gm = input["VBM_GM"]
        # Test wrong masks definitions (more than one key per dict)
        with pytest.raises(ValueError, match=r"only one key"):
            get_mask(masks={"GM_prob0.2": {}, "Other": {}}, target_data=vbm_gm)

        # Test wrong masks definitions (pass paramaeters to non-callable mask)
        with pytest.raises(ValueError, match=r"callable params"):
            get_mask(masks={"GM_prob0.2": {"param": 1}}, target_data=vbm_gm)

        # Pass only parametesr to the intersection function
        with pytest.raises(
            ValueError, match=r" At least one mask is required."
        ):
            get_mask(masks={"threshold": 1}, target_data=vbm_gm)

        # Pass parameters to the intersection function when only one mask
        with pytest.raises(
            ValueError, match=r"parameters to the intersection"
        ):
            get_mask(
                masks=["GM_prob0.2", {"threshold": 1}], target_data=vbm_gm
            )

        # Test "inherited" masks errors

        # 1) No extra_data parameter
        with pytest.raises(ValueError, match=r"no extra data was passed"):
            get_mask(masks="inherit", target_data=vbm_gm)

        extra_input = {"VBM_MASK": {}}

        # 2) No mask_item key in target_data
        with pytest.raises(ValueError, match=r"no mask item was specified"):
            get_mask(
                masks="inherit", target_data=vbm_gm, extra_input=extra_input
            )

        # 3) mask_item not in extra data
        with pytest.raises(ValueError, match=r"does not exist"):
            vbm_gm["mask_item"] = "wrong"
            get_mask(
                masks="inherit", target_data=vbm_gm, extra_input=extra_input
            )


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
    with SPMAuditoryTestingDataGrabber() as dg:
        input = dg["sub001"]
        input = reader.fit_transform(input)
        bold = input["BOLD"]
        bold_img = bold["data"]

        if params is None:
            params = {}
            mask_spec = mask_name
        else:
            mask_spec = {mask_name: params}

        mask = get_mask(masks=mask_spec, target_data=bold)

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


def test_get_mask_inherit() -> None:
    """Test using the inherit mask functionality."""
    reader = DefaultDataReader()
    with SPMAuditoryTestingDataGrabber() as dg:
        input = dg["sub001"]
        input = reader.fit_transform(input)
        # Compute brain mask using nilearn
        gm_mask = compute_brain_mask(input["BOLD"]["data"], threshold=0.2)

        # Get mask using the compute_brain_mask function
        mask1 = get_mask(
            masks={"compute_brain_mask": {"threshold": 0.2}},
            target_data=input["BOLD"],
        )

        # Now get the mask using the inherit functionality, passing the
        # computed mask as extra data
        extra_input = {"BOLD_MASK": {"data": gm_mask}}
        input["BOLD"]["mask_item"] = "BOLD_MASK"
        mask2 = get_mask(
            masks="inherit", target_data=input["BOLD"], extra_input=extra_input
        )

        # Both masks should be equal
        assert_array_equal(mask1.get_fdata(), mask2.get_fdata())


@pytest.mark.parametrize(
    "masks,params",
    [
        (["GM_prob0.2", "compute_brain_mask"], {}),
        (
            ["GM_prob0.2", "compute_brain_mask"],
            {"threshold": 0.2},
        ),
    ],
)
def test_get_mask_multiple(
    masks: Union[str, Dict, List[Union[Dict, str]]], params: Dict
) -> None:
    """Test getting multiple masks.

    Parameters
    ----------
    masks : str, dict, list of str or dict
        Masks to get, junifer style.
    params : dict
        Parameters to pass to the intersect_masks function.
    """
    reader = DefaultDataReader()
    with SPMAuditoryTestingDataGrabber() as dg:
        input = dg["sub001"]
        input = reader.fit_transform(input)
        if not isinstance(masks, list):
            junifer_masks = [masks]
        else:
            junifer_masks = masks.copy()
        if len(params) > 0:
            # Convert params to junifer style (one dict per param)
            junifer_params = [{k: params[k]} for k in params.keys()]
            junifer_masks.extend(junifer_params)
        target_img = input["BOLD"]["data"]
        resolution = np.min(target_img.header.get_zooms()[:3])

        computed = get_mask(masks=junifer_masks, target_data=input["BOLD"])

        masks_names = [
            next(iter(x.keys())) if isinstance(x, dict) else x for x in masks
        ]

        mask_funcs = [
            x
            for x in masks_names
            if _available_masks[x]["family"] == "Callable"
        ]
        mask_files = [
            x
            for x in masks_names
            if _available_masks[x]["family"] != "Callable"
        ]

        mask_imgs = [
            load_mask(t_mask, path_only=False, resolution=resolution)[0]
            for t_mask in mask_files
        ]

        for t_func in mask_funcs:
            mask_imgs.append(_available_masks[t_func]["func"](target_img))

        mask_imgs = [
            resample_to_img(
                t_mask,
                target_img,
                interpolation="nearest",
                copy=True,
            )
            for t_mask in mask_imgs
        ]

        expected = intersect_masks(mask_imgs, **params)
        assert_array_equal(computed.get_fdata(), expected.get_fdata())


def test_get_mask_multiple_incorrect_space() -> None:
    """Test incorrect space error for getting multiple masks."""
    reader = DefaultDataReader()
    with SPMAuditoryTestingDataGrabber() as dg:
        input = dg["sub001"]
        input = reader.fit_transform(input)

        with pytest.raises(RuntimeError, match="unable to merge."):
            get_mask(
                masks=[
                    "GM_prob0.2",
                    "compute_brain_mask",
                    "fetch_icbm152_brain_gm_mask",
                ],
                target_data=input["BOLD"],
            )
