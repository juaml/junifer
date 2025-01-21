"""Provide tests for masks."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Vera Komeyer <v.komeyer@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import socket
from pathlib import Path
from typing import Callable, Optional, Union

import nibabel as nib
import numpy as np
import pytest
from nilearn.image import resample_to_img
from nilearn.masking import (
    compute_background_mask,
    compute_epi_mask,
    intersect_masks,
)
from numpy.testing import assert_array_almost_equal, assert_array_equal

from junifer.data import MaskRegistry
from junifer.data.masks import compute_brain_mask
from junifer.data.masks._masks import (
    _load_ukb_mask,
    _load_vickery_patil_mask,
)
from junifer.datagrabber import DMCC13Benchmark
from junifer.datareader import DefaultDataReader
from junifer.testing.datagrabbers import (
    OasisVBMTestingDataGrabber,
    PartlyCloudyTestingDataGrabber,
    SPMAuditoryTestingDataGrabber,
)


@pytest.mark.parametrize(
    "mask_type, threshold",
    [
        ("brain", 0.2),
        ("brain", 0.5),
        ("brain", 0.8),
        ("gm", 0.2),
        ("gm", 0.5),
        ("gm", 0.8),
        ("wm", 0.2),
        ("wm", 0.5),
        ("wm", 0.8),
    ],
)
def test_compute_brain_mask(mask_type: str, threshold: float) -> None:
    """Test compute_brain_mask().

    Parameters
    ----------
    mask_type : str
        The parametrized mask type.
    threshold : float
        The parametrized threshold.

    """
    with PartlyCloudyTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        mask = compute_brain_mask(
            target_data=element_data["BOLD"],
            mask_type=mask_type,
        )
        assert isinstance(mask, nib.nifti1.Nifti1Image)


@pytest.mark.skipif(
    socket.gethostname() != "juseless",
    reason="only for juseless",
)
@pytest.mark.parametrize(
    "mask_type",
    [
        "brain",
        "gm",
        "wm",
    ],
)
def test_compute_brain_mask_for_native(mask_type: str) -> None:
    """Test compute_brain_mask().

    Parameters
    ----------
    mask_type : str
        The parametrized mask type.

    """
    with DMCC13Benchmark(
        types=["BOLD"],
        sessions=["ses-wave1bas"],
        tasks=["Rest"],
        phase_encodings=["AP"],
        runs=["1"],
        native_t1w=True,
    ) as dg:
        element_data = DefaultDataReader().fit_transform(
            dg[("sub-f1031ax", "ses-wave1bas", "Rest", "AP", "1")]
        )
        mask = compute_brain_mask(
            target_data=element_data["BOLD"],
            extra_input=None,
            mask_type=mask_type,
        )
        assert isinstance(mask, nib.nifti1.Nifti1Image)


def test_register_built_in_check() -> None:
    """Test mask registration check for built-in masks."""
    with pytest.raises(ValueError, match=r"built-in mask"):
        MaskRegistry().register(
            name="GM_prob0.2",
            mask_path="testmask.nii.gz",
            space="MNI",
            overwrite=True,
        )


def test_list_incorrect() -> None:
    """Test incorrect information check for list masks."""
    assert "testmask" not in MaskRegistry().list


def test_register_already_registered() -> None:
    """Test mask registration check for already registered."""
    # Register custom mask
    MaskRegistry().register(
        name="testmask",
        mask_path="testmask.nii.gz",
        space="MNI",
    )
    out = MaskRegistry().load("testmask", path_only=True)
    assert out[1] is not None
    assert out[1].name == "testmask.nii.gz"

    # Try registering again
    with pytest.raises(ValueError, match=r"already registered."):
        MaskRegistry().register(
            name="testmask",
            mask_path="testmask.nii.gz",
            space="MNI",
        )
    MaskRegistry().register(
        name="testmask",
        mask_path="testmask2.nii.gz",
        space="MNI",
        overwrite=True,
    )

    out = MaskRegistry().load("testmask", path_only=True)
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
def test_register(
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
    MaskRegistry().register(
        name=name,
        mask_path=mask_path,
        space=space,
        overwrite=overwrite,
    )
    # List available mask and check registration
    assert name in MaskRegistry().list
    # Load registered mask
    _, fname, mask_space = MaskRegistry().load(name=name, path_only=True)
    # Check values for registered mask
    assert fname is not None
    assert fname.name == f"{name}.nii.gz"
    assert space == mask_space


@pytest.mark.parametrize(
    "mask_name",
    [
        "GM_prob0.2",
        "GM_prob0.2_cortex",
        "UKB_15K_GM",
    ],
)
def test_list_correct(mask_name: str) -> None:
    """Test correct information check for list masks.

    Parameters
    ----------
    mask_name : str
        The parametrized mask name.

    """
    assert mask_name in MaskRegistry().list


def test_load_incorrect() -> None:
    """Test loading of invalid masks."""
    with pytest.raises(ValueError, match=r"not found"):
        MaskRegistry().load("wrongmask")


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
    pixdim: list[float],
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
    mask, mask_fname, space = MaskRegistry().load(name, resolution=resolution)
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


def test_ukb() -> None:
    """Test UKB mask."""
    mask, mask_fname, space = MaskRegistry().load("UKB_15K_GM", resolution=2.0)
    assert_array_almost_equal(mask.header["pixdim"][1:4], 2.0)  # type: ignore
    assert space == "MNI152NLin6Asym"
    assert mask_fname is not None
    assert mask_fname.name == "UKB_15K_GM_template.nii.gz"


def test_ukb_error() -> None:
    """Test error for UKB mask."""
    with pytest.raises(ValueError, match=r"find a UKB mask "):
        _load_ukb_mask(name="wrong")


def test_get() -> None:
    """Test tailored mask fetch."""
    with OasisVBMTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        vbm_gm = element_data["VBM_GM"]
        vbm_gm_img = vbm_gm["data"]
        mask = MaskRegistry().get(
            masks="compute_brain_mask", target_data=vbm_gm
        )

        assert mask.shape == vbm_gm_img.shape
        assert_array_equal(mask.affine, vbm_gm_img.affine)

        raw_mask_callable, _, _ = MaskRegistry().load(
            "compute_brain_mask", resolution=1.5
        )
        raw_mask_img = raw_mask_callable(vbm_gm)  # type: ignore
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

    MaskRegistry()._registry["identity"] = {
        "family": "Callable",
        "func": ident,
        "space": "MNI152Lin",
    }
    with OasisVBMTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        vbm_gm = element_data["VBM_GM"]
        vbm_gm_img = vbm_gm["data"]
        mask = MaskRegistry().get(masks="identity", target_data=vbm_gm)

        assert_array_equal(mask.get_fdata(), vbm_gm_img.get_fdata())

    del MaskRegistry()._registry["identity"]


def test_get_errors() -> None:
    """Test passing wrong parameters to fetch mask."""
    with OasisVBMTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        vbm_gm = element_data["VBM_GM"]
        # Test wrong masks definitions (more than one key per dict)
        with pytest.raises(ValueError, match=r"only one key"):
            MaskRegistry().get(
                masks={"GM_prob0.2": {}, "Other": {}}, target_data=vbm_gm
            )

        # Test wrong masks definitions (pass paramaeters to non-callable mask)
        with pytest.raises(ValueError, match=r"callable params"):
            MaskRegistry().get(
                masks={"GM_prob0.2": {"param": 1}}, target_data=vbm_gm
            )

        # Pass only parameters to the intersection function
        with pytest.raises(
            ValueError, match=r" At least one mask is required."
        ):
            MaskRegistry().get(masks={"threshold": 1}, target_data=vbm_gm)

        # Pass parameters to the intersection function when only one mask
        with pytest.raises(
            ValueError, match=r"parameters to the intersection"
        ):
            MaskRegistry().get(
                masks=["compute_brain_mask", {"threshold": 1}],
                target_data=vbm_gm,
            )

        # Test "inherited" masks error
        with pytest.raises(ValueError, match=r"provide `mask`"):
            MaskRegistry().get(masks="inherit", target_data=vbm_gm)


@pytest.mark.parametrize(
    "mask_name,function,params,resample",
    [
        ("compute_background_mask", compute_background_mask, None, False),
        ("compute_epi_mask", compute_epi_mask, None, False),
    ],
)
def test_nilearn_compute_masks(
    mask_name: str,
    function: Callable,
    params: Union[dict, None],
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
    with SPMAuditoryTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub001"])
        bold = element_data["BOLD"]
        bold_img = bold["data"]

        if params is None:
            params = {}
            mask_spec = mask_name
        else:
            mask_spec = {mask_name: params}

        mask = MaskRegistry().get(masks=mask_spec, target_data=bold)

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


def test_get_inherit() -> None:
    """Test mask fetch using the inherit mask functionality."""
    with SPMAuditoryTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub001"])
        # Compute brain mask using nilearn
        gm_mask = compute_brain_mask(element_data["BOLD"], threshold=0.2)

        # Get mask using the compute_brain_mask function
        mask1 = MaskRegistry().get(
            masks={"compute_brain_mask": {"threshold": 0.2}},
            target_data=element_data["BOLD"],
        )

        # Now get the mask using the inherit functionality, passing the
        # computed mask as the data
        bold_dict = element_data["BOLD"]
        bold_dict["mask"] = {
            "data": gm_mask,
            "space": element_data["BOLD"]["space"],
        }
        mask2 = MaskRegistry().get(
            masks="inherit",
            target_data=bold_dict,
        )

        # Both masks should be equal
        assert_array_equal(mask1.get_fdata(), mask2.get_fdata())


@pytest.mark.parametrize(
    "masks,params",
    [
        (["compute_brain_mask", "compute_background_mask"], {}),
        (["compute_brain_mask", "compute_epi_mask"], {}),
    ],
)
def test_get_multiple(
    masks: Union[str, dict, list[Union[dict, str]]], params: dict
) -> None:
    """Test getting multiple masks.

    Parameters
    ----------
    masks : str, dict, list of str or dict
        Masks to get, junifer style.
    params : dict
        Parameters to pass to the intersect_masks function.

    """
    with SPMAuditoryTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub001"])
        if not isinstance(masks, list):
            junifer_masks = [masks]
        else:
            junifer_masks = masks.copy()
        if len(params) > 0:
            # Convert params to junifer style (one dict per param)
            junifer_params = [{k: params[k]} for k in params.keys()]
            junifer_masks.extend(junifer_params)
        target_img = element_data["BOLD"]["data"]
        resolution = np.min(target_img.header.get_zooms()[:3])

        computed = MaskRegistry().get(
            masks=junifer_masks, target_data=element_data["BOLD"]
        )

        masks_names = [
            next(iter(x.keys())) if isinstance(x, dict) else x for x in masks
        ]

        mask_funcs = [
            x
            for x in masks_names
            if MaskRegistry()._registry[x]["family"] == "Callable"
        ]
        mask_files = [
            x
            for x in masks_names
            if MaskRegistry()._registry[x]["family"] != "Callable"
        ]

        mask_imgs = [
            MaskRegistry().load(
                t_mask, path_only=False, resolution=resolution
            )[0]
            for t_mask in mask_files
        ]

        for t_func in mask_funcs:
            # Bypass for custom mask
            if t_func == "compute_brain_mask":
                mask_imgs.append(
                    MaskRegistry()._registry[t_func]["func"](
                        element_data["BOLD"]
                    )
                )
            else:
                mask_imgs.append(
                    MaskRegistry()._registry[t_func]["func"](target_img)
                )

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
