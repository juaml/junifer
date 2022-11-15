"""Provide JuniferNiftiSpheresMasker class."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import TYPE_CHECKING, Callable, List, Optional, Tuple, Union

import numpy as np
from nilearn._utils.class_inspect import get_params
from nilearn._utils.niimg import img_data_dtype
from nilearn._utils.niimg_conversions import check_niimg_4d
from nilearn.maskers import NiftiSpheresMasker
from nilearn.maskers.base_masker import _filter_and_extract
from nilearn.maskers.nifti_spheres_masker import _iter_signals_from_spheres

from ...utils import raise_error


if TYPE_CHECKING:
    from pathlib import Path

    from nibabel import Nifti1Image, Nifti2Image
    from numpy.typing import ArrayLike, DTypeLike
    from pandas import DataFrame


"""
New BSD License

Copyright (c) 2007 - 2022 The nilearn developers.
All rights reserved.


Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

  a. Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.
  b. Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.
  c. Neither the name of the nilearn developers nor the names of
     its contributors may be used to endorse or promote products
     derived from this software without specific prior written
     permission.


THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
DAMAGE.
"""


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
    ) -> Tuple["ArrayLike", None]:
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

    Parameters
    ----------
    seeds : list of triplet of coordinates in native space
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
    dtype : any type that can be coerced into a numpy dtype or "auto", optional
        The dtype for the extraction. If "auto", the data will be converted to
        int32 if dtype is discrete and float32 if it is continuous
        (default None).
    **kwargs
        Keyword arguments are passed to the
        :func:`nilearn.maskers.NiftiSpheresMasker`.

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
            str, "Path", "ArrayLike", "DataFrame", List, None
        ] = None,
        sample_mask: Union["ArrayLike", List, Tuple, None] = None,
    ) -> "ArrayLike":
        """Extract signals from a single 4D niimg.

        Parameters
        ----------
        imgs : 3D/4D Niimg-like object
            Images to process.
            If a 3D niimg is provided, a singleton dimension will be added to
            the output to represent the single scan in the niimg.
        confounds : CSV file or array-like or pandas.DataFrame, optional
            This parameter is passed to :func:`nilearn.signal.clean`.
            Please see the related documentation for details.
            shape: (number of scans, number of confounds)
        sample_mask : Any type compatible with numpy-array indexing, optional
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
