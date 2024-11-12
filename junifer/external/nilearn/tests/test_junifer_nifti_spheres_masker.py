"""Provide tests for JuniferNiftiSpheresMasker class."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import warnings

import nibabel
import numpy as np
import pytest
from nilearn._utils import data_gen
from nilearn.image import get_data
from nilearn.maskers import NiftiSpheresMasker
from numpy.testing import assert_array_equal

from junifer.external.nilearn import JuniferNiftiSpheresMasker


# New BSD License

# Copyright (c) The nilearn developers.
# All rights reserved.


# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

#   a. Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#   b. Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#   c. Neither the name of the nilearn developers nor the names of
#      its contributors may be used to endorse or promote products
#      derived from this software without specific prior written
#      permission.


# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.


def test_seed_extraction() -> None:
    """Test seed extraction."""
    data = np.random.RandomState(42).random_sample((3, 3, 3, 5))
    img = nibabel.Nifti1Image(data, np.eye(4))
    masker = JuniferNiftiSpheresMasker(seeds=[(1, 1, 1)])
    # Test the fit
    masker.fit()
    # Test the transform
    s = masker.transform(img)
    assert_array_equal(s[:, 0], data[1, 1, 1])


def test_sphere_extraction() -> None:
    """Test sphere extraction."""
    data = np.random.RandomState(42).random_sample((3, 3, 3, 5))
    img = nibabel.Nifti1Image(data, np.eye(4))
    masker = JuniferNiftiSpheresMasker(seeds=[(1, 1, 1)], radius=1)

    # Check attributes defined at fit
    assert not hasattr(masker, "seeds_")
    assert not hasattr(masker, "n_elements_")

    masker.fit()

    # Check attributes defined at fit
    assert hasattr(masker, "seeds_")
    assert hasattr(masker, "n_elements_")
    assert masker.n_elements_ == 1

    # Test the fit
    masker.fit()

    # Test the transform
    s = masker.transform(img)
    mask = np.zeros((3, 3, 3), dtype=bool)
    mask[:, 1, 1] = True
    mask[1, :, 1] = True
    mask[1, 1, :] = True
    assert_array_equal(s[:, 0], np.mean(data[mask], axis=0))

    # Now with a mask
    mask_img = np.zeros((3, 3, 3))
    mask_img[1, :, :] = 1
    mask_img = nibabel.Nifti1Image(mask_img, np.eye(4))
    masker = JuniferNiftiSpheresMasker(
        seeds=[(1, 1, 1)],
        radius=1,
        mask_img=mask_img,
    )
    masker.fit()
    s = masker.transform(img)
    assert_array_equal(
        s[:, 0],
        np.mean(
            data[np.logical_and(mask, get_data(mask_img))],
            axis=0,
        ),
    )


def test_anisotropic_sphere_extraction() -> None:
    """Test anisotropic sphere extraction."""
    data = np.random.RandomState(42).random_sample((3, 3, 3, 5))
    affine = np.eye(4)
    affine[0, 0] = 2
    affine[2, 2] = 2
    img = nibabel.Nifti1Image(data, affine)
    masker = JuniferNiftiSpheresMasker(seeds=[(2, 1, 2)], radius=1)
    # Test the fit
    masker.fit()
    # Test the transform
    s = masker.transform(img)
    mask = np.zeros((3, 3, 3), dtype=bool)
    mask[1, :, 1] = True
    assert_array_equal(s[:, 0], np.mean(data[mask], axis=0))
    # Now with a mask
    mask_img = np.zeros((3, 2, 3))
    mask_img[1, 0, 1] = 1
    affine_2 = affine.copy()
    affine_2[0, 0] = 4
    mask_img = nibabel.Nifti1Image(mask_img, affine=affine_2)
    masker = JuniferNiftiSpheresMasker(
        seeds=[(2, 1, 2)],
        radius=1,
        mask_img=mask_img,
    )

    masker.fit()
    s = masker.transform(img)
    assert_array_equal(s[:, 0], data[1, 0, 1])


def test_errors() -> None:
    """Test errors."""
    masker = JuniferNiftiSpheresMasker(seeds=([1, 2]), radius=0.2)
    with pytest.raises(ValueError, match="Seeds must be a list .+"):
        masker.fit()


def test_nifti_spheres_masker_overlap() -> None:
    """Test overlapping sphere extraction."""
    # Test resampling in NiftiMapsMasker
    affine = np.eye(4)
    shape = (5, 5, 5)

    data = np.random.RandomState(42).random_sample((*shape, 5))
    fmri_img = nibabel.Nifti1Image(data, affine)

    seeds = [(0, 0, 0), (2, 2, 2)]

    overlapping_masker = JuniferNiftiSpheresMasker(
        seeds,
        radius=1,
        allow_overlap=True,
    )
    overlapping_masker.fit_transform(fmri_img)
    overlapping_masker = JuniferNiftiSpheresMasker(
        seeds,
        radius=2,
        allow_overlap=True,
    )
    overlapping_masker.fit_transform(fmri_img)

    noverlapping_masker = JuniferNiftiSpheresMasker(
        seeds,
        radius=1,
        allow_overlap=False,
    )
    noverlapping_masker.fit_transform(fmri_img)
    noverlapping_masker = JuniferNiftiSpheresMasker(
        seeds,
        radius=2,
        allow_overlap=False,
    )
    with pytest.raises(ValueError, match="Overlap detected"):
        noverlapping_masker.fit_transform(fmri_img)


def test_small_radius() -> None:
    """Test sphere extraction with small radius."""
    affine = np.eye(4)
    shape = (3, 3, 3)

    data = np.random.RandomState(42).random_sample(shape)
    mask = np.zeros(shape)
    mask[1, 1, 1] = 1
    mask[2, 2, 2] = 1
    affine = np.eye(4) * 1.2
    seed = (1.4, 1.4, 1.4)

    masker = JuniferNiftiSpheresMasker(
        seeds=[seed],
        radius=0.1,
        mask_img=nibabel.Nifti1Image(mask, affine),
    )
    masker.fit_transform(nibabel.Nifti1Image(data, affine))

    # Test if masking is taken into account
    mask[1, 1, 1] = 0
    mask[1, 1, 0] = 1

    masker = JuniferNiftiSpheresMasker(
        seeds=[seed],
        radius=0.1,
        mask_img=nibabel.Nifti1Image(mask, affine),
    )

    out = masker.fit_transform(nibabel.Nifti1Image(data, affine))
    assert np.isnan(out).all()

    masker = JuniferNiftiSpheresMasker(
        seeds=[seed],
        radius=1.6,
        mask_img=nibabel.Nifti1Image(mask, affine),
    )
    masker.fit_transform(nibabel.Nifti1Image(data, affine))


def test_is_nifti_spheres_masker_give_nans() -> None:
    """Test NaN interaction with masker."""
    affine = np.eye(4)

    data_with_nans = np.zeros((10, 10, 10), dtype=np.float32)
    data_with_nans[:, :, :] = np.nan

    data_without_nans = np.random.RandomState(42).random_sample((9, 9, 9))
    indices = np.nonzero(data_without_nans)

    # Leaving nans outside of some data
    data_with_nans[indices] = data_without_nans[indices]
    img = nibabel.Nifti1Image(data_with_nans, affine)
    seed = [(7, 7, 7)]

    # Interaction of seed with nans
    masker = JuniferNiftiSpheresMasker(seeds=seed, radius=2.0)
    assert not np.isnan(np.sum(masker.fit_transform(img)))

    mask = np.ones((9, 9, 9))
    mask_img = nibabel.Nifti1Image(mask, affine)
    # When mask_img is provided, the seed interacts within the brain, so no nan
    masker = JuniferNiftiSpheresMasker(
        seeds=seed,
        radius=2.0,
        mask_img=mask_img,
    )
    assert not np.isnan(np.sum(masker.fit_transform(img)))


def test_standardization() -> None:
    """Test standardization."""
    data = np.random.RandomState(42).random_sample((3, 3, 3, 5))
    img = nibabel.Nifti1Image(data, np.eye(4))

    # test zscore
    masker = JuniferNiftiSpheresMasker(seeds=[(1, 1, 1)], standardize="zscore")
    # Test the fit
    s = masker.fit_transform(img)

    np.testing.assert_almost_equal(s.mean(), 0)
    np.testing.assert_almost_equal(s.std(), 1)

    # test psc
    masker = JuniferNiftiSpheresMasker(seeds=[(1, 1, 1)], standardize="psc")
    # Test the fit
    s = masker.fit_transform(img)

    np.testing.assert_almost_equal(s.mean(), 0)
    np.testing.assert_almost_equal(
        s.ravel(),
        data[1, 1, 1] / data[1, 1, 1].mean() * 100 - 100,
    )


def test_nifti_spheres_masker_inverse_transform() -> None:
    """Test inverse transform."""
    data = np.random.RandomState(42).random_sample((3, 3, 3, 5))
    masker = JuniferNiftiSpheresMasker(seeds=[(1, 1, 1)], radius=1)
    with pytest.raises(
        NotImplementedError,
        match="some of which are non-reversible",
    ):
        masker.inverse_transform(data[0, 0, 0, :])


def test_nifti_spheres_masker_io_shapes() -> None:
    """Ensure that masker handles 1D/2D/3D/4D data appropriately.

    transform(4D image) --> 2D output, no warning
    transform(3D image) --> 2D output, DeprecationWarning

    """
    n_regions, n_volumes = 2, 5
    shape_3d = (10, 11, 12)
    shape_4d = (10, 11, 12, n_volumes)
    affine = np.eye(4)

    img_4d, mask_img = data_gen.generate_random_img(
        shape_4d,
        affine=affine,
    )
    img_3d, _ = data_gen.generate_random_img(shape_3d, affine=affine)

    masker = JuniferNiftiSpheresMasker(
        seeds=[(1, 1, 1), (4, 4, 4)],  # number of tuples equal to n_regions
        radius=1,
        mask_img=mask_img,
    )
    masker.fit()

    # DeprecationWarning *should* be raised for 3D inputs
    with pytest.warns(DeprecationWarning, match="Starting in version 0.12"):
        test_data = masker.transform(img_3d)
        assert test_data.shape == (1, n_regions)

    # DeprecationWarning should *not* be raised for 4D inputs
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "error",
            message="Starting in version 0.12",
            category=DeprecationWarning,
        )
        test_data = masker.transform(img_4d)
        assert test_data.shape == (n_volumes, n_regions)


@pytest.mark.parametrize(
    "shape",
    [
        (10, 11, 12),
        (10, 11, 12, 5),
    ],
)
@pytest.mark.parametrize(
    "radius, allow_overlap",
    [
        (2.0, True),
        (2.0, False),
        (3.0, True),
        (4.0, True),
        (5.0, True),
    ],
)
@pytest.mark.parametrize(
    "coords",
    [
        [(1, 1, 1)],
        [(1, 1, 1), (4, 4, 4)],
        [(1, 1, 1), (4, 4, 4), (10, 10, 10)],
    ],
)
def test_junifer_and_nilearn_mean_agg_are_equal(
    shape: tuple[int, ...],
    radius: float,
    allow_overlap: bool,
    coords: list[tuple[int, int, int]],
) -> None:
    """Test junifer's masker behaves same as nilearn's when agg is mean.

    Parameters
    ----------
    shape : tuple of int
        The parametrized shape of the input image.
    radius : float
        The parametrized radius of the spheres.
    allow_overlap : bool
        The parametrized option to overlap spheres or not.
    coords : list of tuple of int, int and int
        The parametrized seeds.

    """
    # Set affine
    affine = np.eye(4)
    # Generate random image
    input_img, mask_img = data_gen.generate_random_img(
        shape=shape,
        affine=affine,
    )
    # Compute junifer's version
    junifer_masker = JuniferNiftiSpheresMasker(
        seeds=coords,
        radius=radius,
        allow_overlap=allow_overlap,
        mask_img=mask_img,
    )
    junifer_output = junifer_masker.fit_transform(input_img)
    # Compute nilearn's version
    nilearn_masker = NiftiSpheresMasker(
        seeds=coords,
        radius=radius,
        allow_overlap=allow_overlap,
        mask_img=mask_img,
    )
    nilearn_output = nilearn_masker.fit_transform(input_img)
    # Checks
    assert junifer_output.shape == nilearn_output.shape
    np.testing.assert_almost_equal(junifer_output, nilearn_output)
