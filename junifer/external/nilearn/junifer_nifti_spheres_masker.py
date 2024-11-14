"""Provide JuniferNiftiSpheresMasker class."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import TYPE_CHECKING, Callable, Optional, Union

import numpy as np
from nilearn import image, masking
from nilearn._utils.class_inspect import get_params
from nilearn._utils.niimg import img_data_dtype
from nilearn._utils.niimg_conversions import (
    check_niimg_3d,
    check_niimg_4d,
    safe_get_data,
)
from nilearn.maskers import NiftiSpheresMasker
from nilearn.maskers.base_masker import _filter_and_extract
from sklearn import neighbors

from ...utils import raise_error, warn_with_log


if TYPE_CHECKING:
    from pathlib import Path

    from nibabel import Nifti1Image, Nifti2Image
    from numpy.typing import ArrayLike, DTypeLike
    from pandas import DataFrame


__all__ = ["JuniferNiftiSpheresMasker"]


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


def _apply_mask_and_get_affinity(
    seeds, niimg, radius, allow_overlap, mask_img=None
):
    """Apply mask and get affinity matrix for given seeds.

    Utility function to get only the rows which are occupied by sphere at
    given seed locations and the provided radius. Rows are in target_affine and
    target_shape space.

    Parameters
    ----------
    seeds : List of triplets of coordinates in native space
        Seed definitions. List of coordinates of the seeds in the same space
        as target_affine.
    niimg : 3D/4D Niimg-like object
        See :ref:`extracting_data`.
        Images to process.
        If a 3D niimg is provided, a singleton dimension will be added to
        the output to represent the single scan in the niimg.
    radius : float
        Indicates, in millimeters, the radius for the sphere around the seed.
    allow_overlap : boolean
        If False, a ValueError is raised if VOIs overlap
    mask_img : Niimg-like object, optional
        Mask to apply to regions before extracting signals. If niimg is None,
        mask_img is used as a reference space in which the spheres 'indices are
        placed.

    Returns
    -------
    X : 2D numpy.ndarray
        Signal for each brain voxel in the (masked) niimgs.
        shape: (number of scans, number of voxels)
    A : scipy.sparse.lil_matrix
        Contains the boolean indices for each sphere.
        shape: (number of seeds, number of voxels)

    Raises
    ------
    ValueError
        If ``niimg`` and ``mask_img`` are both provided or
        if overlap is detected between spheres.

    Warns
    -----
    RuntimeWarning
        If the provided images contain NaN, they will be converted to zeroes.

    """
    seeds = list(seeds)

    # Compute world coordinates of all in-mask voxels.
    if niimg is None:
        mask, affine = masking.load_mask_img(mask_img)
        # Get coordinate for all voxels inside of mask
        mask_coords = np.asarray(np.nonzero(mask)).T.tolist()
        X = None

    elif mask_img is not None:
        affine = niimg.affine
        mask_img = check_niimg_3d(mask_img)
        mask_img = image.resample_img(
            mask_img,
            target_affine=affine,
            target_shape=niimg.shape[:3],
            interpolation="nearest",
        )
        mask, _ = masking.load_mask_img(mask_img)
        mask_coords = list(zip(*np.where(mask != 0)))

        X = masking.apply_mask_fmri(niimg, mask_img)

    elif niimg is not None:
        affine = niimg.affine
        if np.isnan(np.sum(safe_get_data(niimg))):
            warn_with_log(
                "The imgs you have fed into fit_transform() contains NaN "
                "values which will be converted to zeroes."
            )
            X = safe_get_data(niimg, True).reshape([-1, niimg.shape[3]]).T
        else:
            X = safe_get_data(niimg).reshape([-1, niimg.shape[3]]).T

        mask_coords = list(np.ndindex(niimg.shape[:3]))

    else:
        raise_error("Either a niimg or a mask_img must be provided.")

    # For each seed, get coordinates of nearest voxel
    nearests = []
    for sx, sy, sz in seeds:
        nearest = np.round(
            image.resampling.coord_transform(sx, sy, sz, np.linalg.inv(affine))
        )
        nearest = nearest.astype(int)
        nearest = (nearest[0], nearest[1], nearest[2])
        try:
            nearests.append(mask_coords.index(nearest))
        except ValueError:
            nearests.append(None)

    mask_coords = np.asarray(list(zip(*mask_coords)))
    mask_coords = image.resampling.coord_transform(
        mask_coords[0], mask_coords[1], mask_coords[2], affine
    )
    mask_coords = np.asarray(mask_coords).T

    clf = neighbors.NearestNeighbors(radius=radius)
    A = clf.fit(mask_coords).radius_neighbors_graph(seeds)
    A = A.tolil()
    for i, nearest in enumerate(nearests):
        if nearest is None:
            continue

        A[i, nearest] = True

    # Include the voxel containing the seed itself if not masked
    mask_coords = mask_coords.astype(int).tolist()
    for i, seed in enumerate(seeds):
        try:
            A[i, mask_coords.index(list(map(int, seed)))] = True
        except ValueError:
            # seed is not in the mask
            pass

    if (not allow_overlap) and np.any(A.sum(axis=0) >= 2):
        raise_error("Overlap detected between spheres")

    return X, A


def _iter_signals_from_spheres(
    seeds, niimg, radius, allow_overlap, mask_img=None
):
    """Iterate over spheres.

    Parameters
    ----------
    seeds : :obj:`list` of triplets of coordinates in native space
        Seed definitions. List of coordinates of the seeds in the same space
        as the images (typically MNI or TAL).
    niimg : 3D/4D Niimg-like object
        See :ref:`extracting_data`.
        Images to process.
        If a 3D niimg is provided, a singleton dimension will be added to
        the output to represent the single scan in the niimg.
    radius: float
        Indicates, in millimeters, the radius for the sphere around the seed.
    allow_overlap: boolean
        If False, an error is raised if the maps overlaps (ie at least two
        maps have a non-zero value for the same voxel).
    mask_img : Niimg-like object, optional
        See :ref:`extracting_data`.
        Mask to apply to regions before extracting signals.

    """
    X, A = _apply_mask_and_get_affinity(
        seeds, niimg, radius, allow_overlap, mask_img=mask_img
    )
    for row in A.rows:
        yield X[:, row]


class _JuniferExtractionFunctor:
    """Functor to extract signals from spheres.

    Parameters
    ----------
    seeds_ : list of triple of coordinates in native space
        Seed definitions. List of coordinates of the seeds in the same space
        as the images (typically MNI or TAL).
    radius : float
        Indicates, in millimeters, the radius for the sphere around the seed.
    mask_img : Niimg-like object
        Mask to apply to regions before extracting signals.
    agg_func : callable
        The function to aggregate signals using.
    allow_overlap : bool
        If False, an error is raised if the maps overlap.
    dtype : any type that can be coerced into a numpy dtype or "auto"
        The dtype for the extraction. If "auto", the data will be converted to
        int32 if dtype is discrete and float32 if it is continuous.

    """

    func_name = "junifer_nifti_spheres_masker_extractor"

    def __init__(
        self,
        seeds_: "ArrayLike",
        radius: Optional[float],
        mask_img: Union["Nifti1Image", "Nifti2Image", None],
        agg_func: Callable,
        allow_overlap: bool,
        dtype: Union["DTypeLike", str, None],
    ) -> None:
        self.seeds_ = seeds_
        self.radius = radius
        self.mask_img = mask_img
        self.agg_func = agg_func
        self.allow_overlap = allow_overlap
        self.dtype = dtype

    def __call__(
        self,
        imgs: Union["Nifti1Image", "Nifti2Image"],
    ) -> tuple["ArrayLike", None]:
        """Implement function call overloading.

        Parameters
        ----------
        imgs : 4D Niimg-like object
           If ``imgs`` is an iterable, checks if data is really 4D. Then,
           considering that it is a list of ``img``, load them one by one.
           If ``img`` is a string, consider it as a path to Nifti image and
           call :func:`nibabel.load` on it.
           If it is an object, check if the affine attribute is present and
           that :func:`nilearn.image.get_data` returns a result, eval raise
           TypeError.

        Raises
        ------
        TypeError
            If ``img`` in ``imgs`` is an object without the affine attribute.

        Returns
        -------
        tuple of numpy.ndarray and None
            The numpy.ndarray returned is the array of extracted signals.

        """
        n_seeds = len(self.seeds_)
        imgs = check_niimg_4d(imgs, dtype=self.dtype)

        signals = np.empty(
            (imgs.shape[3], n_seeds), dtype=img_data_dtype(imgs)
        )
        for i, sphere in enumerate(
            _iter_signals_from_spheres(
                seeds=self.seeds_,
                niimg=imgs,
                radius=self.radius,
                allow_overlap=self.allow_overlap,
                mask_img=self.mask_img,
            )
        ):
            signals[:, i] = self.agg_func(sphere, axis=1)
        return signals, None


class JuniferNiftiSpheresMasker(NiftiSpheresMasker):
    """Class for custom NiftiSpheresMasker.

    Differs from :class:`nilearn.maskers.NiftiSpheresMasker` in the following
    ways:

    * it allows to pass any callable as the ``agg_func`` parameter.
    * empty spheres do not create an error. Instead, ``agg_func`` is applied to
      an empty array and the result is passed.

    Parameters
    ----------
    seeds : list of float
        Seed definitions. List of coordinates of the seeds in the same space
        as the images (typically MNI or TAL).
    radius : float, optional
        Indicates, in millimeters, the radius for the sphere around the seed.
        If None, signal is extracted on a single voxel (default None).
    mask_img : Niimg-like object, optional
        Mask to apply to regions before extracting signals (default None).
    agg_func : callable, optional
        The function to aggregate signals using (default numpy.mean).
    allow_overlap : bool, optional
        If False, an error is raised if the maps overlap (default None).
    dtype : numpy.dtype or "auto", optional
        The dtype for the extraction. If "auto", the data will be converted to
        int32 if dtype is discrete and float32 if it is continuous
        (default None).
    **kwargs
        Keyword arguments are passed to the
        :class:`nilearn.maskers.NiftiSpheresMasker`.

    """

    def __init__(
        self,
        seeds: "ArrayLike",
        radius: Optional[float] = None,
        mask_img: Union["Nifti1Image", "Nifti2Image", None] = None,
        agg_func: Callable = np.mean,
        allow_overlap: bool = False,
        dtype: Union["DTypeLike", str, None] = None,
        **kwargs,  # TODO: to keep or not?
    ) -> None:
        self.agg_func = agg_func
        super().__init__(
            seeds=seeds,
            radius=radius,
            mask_img=mask_img,
            allow_overlap=allow_overlap,
            **kwargs,
        )

    def transform_single_imgs(
        self,
        imgs: Union["Nifti1Image", "Nifti2Image"],
        confounds: Union[
            str, "Path", "ArrayLike", "DataFrame", list, None
        ] = None,
        sample_mask: Union["ArrayLike", list, tuple, None] = None,
    ) -> "ArrayLike":
        """Extract signals from a single 4D niimg.

        Parameters
        ----------
        imgs : 3D/4D Niimg-like object
            Images to process.
            If a 3D niimg is provided, a singleton dimension will be added to
            the output to represent the single scan in the niimg.
        confounds : pandas.DataFrame, optional
            This parameter is passed to :func:`nilearn.signal.clean`.
            Please see the related documentation for details.
            shape: (number of scans, number of confounds)
        sample_mask : np.ndarray, list or tuple, optional
            Masks the niimgs along time/fourth dimension to perform scrubbing
            (remove volumes with high motion) and/or non-steady-state volumes.
            This parameter is passed to :func:`nilearn.signal.clean`.
            shape: (number of scans - number of volumes removed, )

        Returns
        -------
        region_signals : 2D numpy.ndarray
            Signal for each sphere.
            shape: (number of scans, number of spheres)

        Warns
        -----
        DeprecationWarning
            If a 3D niimg input is provided, the current behavior
            (adding a singleton dimension to produce a 2D array) is deprecated.
            Starting in version 0.12, a 1D array will be returned for 3D
            inputs.

        """
        self._check_fitted()

        params = get_params(NiftiSpheresMasker, self)

        # New in nilearn 0.10.1
        if hasattr(self, "clean_kwargs"):
            params["clean_kwargs"] = self.clean_kwargs

        signals, _ = self._cache(
            _filter_and_extract, ignore=["verbose", "memory", "memory_level"]
        )(
            imgs,
            _JuniferExtractionFunctor(
                seeds_=self.seeds_,
                radius=self.radius,
                mask_img=self.mask_img,
                agg_func=self.agg_func,
                allow_overlap=self.allow_overlap,
                dtype=self.dtype,
            ),
            # Pre-processing
            params,
            confounds=confounds,
            sample_mask=sample_mask,
            dtype=self.dtype,
            # Caching
            memory=self.memory,
            memory_level=self.memory_level,
            # kwargs
            verbose=self.verbose,
        )
        return signals

    def inverse_transform(self, region_signals: "ArrayLike") -> "Nifti1Image":
        """Compute voxel signals from spheres signals.

        Parameters
        ----------
        region_signals : 1D/2D numpy.ndarray
            Signal for each region.
            If a 1D array is provided, then the shape should be
            (number of elements,), and a 3D img will be returned.
            If a 2D array is provided, then the shape should be
            (number of scans, number of elements), and a 4D img will be
            returned.

        Returns
        -------
        voxel_signals : nibabel.nifti1.Nifti1Image
            Signal for each sphere.
            shape: (mask_img, number of scans).

        """
        raise_error(
            msg="As this class allows multiple methods of aggregation while "
            "transforming, some of which are non-reversible, "
            "inverse_transform() should not be implemented.",
            klass=NotImplementedError,
        )
