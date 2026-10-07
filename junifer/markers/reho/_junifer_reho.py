"""Provide class for computing regional homogeneity (ReHo) using junifer."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from functools import lru_cache
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    ClassVar,
)

import nibabel as nib
import numpy as np
import scipy as sp
from nilearn import image as nimg

from ...pipeline import WorkDirManager
from ...typing import Dependencies
from ...utils import raise_error
from ...utils.singleton import Singleton
from ..base import logger


if TYPE_CHECKING:
    from nibabel.nifti1 import Nifti1Image


__all__ = ["JuniferReHo"]


class JuniferReHo(metaclass=Singleton):
    """Class for computing ReHo using junifer.

    It's designed as a singleton with caching for efficient computation.

    """

    _DEPENDENCIES: ClassVar[Dependencies] = {"numpy", "nilearn", "scipy"}

    def __del__(self) -> None:
        """Terminate the class."""
        # Clear the computation cache
        logger.debug("Clearing cache for ReHo computation via junifer")
        self.compute.cache_clear()

    @lru_cache(maxsize=None, typed=True)
    def compute(
        self,
        input_path: Path,
        nneigh: int = 27,
        mask_path: Path | None = None,
    ) -> tuple["Nifti1Image", Path]:
        """Compute ReHo map.

        Parameters
        ----------
        input_path : pathlib.Path
            Path to the input data.
        nneigh : {7, 19, 27, 125}, optional
            Number of voxels in the neighbourhood, inclusive. Can be:

            * 7 : for facewise neighbours only
            * 19 : for face- and edge-wise neighbours
            * 27 : for face-, edge-, and node-wise neighbors
            * 125 : for 5x5 cuboidal volume

            (default 27).
        mask_path : pathlib.Path or None, optional
            Path to the mask to restrict the computation to. Voxels outside
            the mask are excluded from every neighbourhood and set to 0 in
            the output. If None, voxels with non-zero time series are used,
            same as AFNI's ``3dReHo`` without ``-mask`` (default None).

        Returns
        -------
        Niimg-like object
            The ReHo map as NIfTI.
        pathlib.Path
            The path to the ReHo map as NIfTI.

        Raises
        ------
        ValueError
            If ``nneigh`` is invalid.

        """
        valid_nneigh = (7, 19, 27, 125)
        if nneigh not in valid_nneigh:
            raise_error(
                f"Invalid value for `nneigh`, should be one of: {valid_nneigh}"
            )

        logger.debug("Creating cache for ReHo computation via junifer")

        # Get scan data
        niimg = nib.load(input_path)
        niimg_data = niimg.get_fdata(caching="unchanged")
        # Get scan dimensions
        n_x, n_y, n_z, n_t = niimg_data.shape

        # Get mask as bool array
        if mask_path is not None:
            logical_mask = np.squeeze(nib.load(mask_path).get_fdata()) != 0
        else:
            # Same as AFNI's 3dReHo without -mask
            logical_mask = np.sum(np.abs(niimg_data), axis=-1) > 1e-6

        # Get rank of every voxel across time series and tied rank correction
        # for every voxel
        ranks_niimg_data, tied_rank_corrections = _rank_with_ties(niimg_data)
        del niimg_data

        # Create mask cluster and set start and end indices
        if nneigh in (7, 19, 27):
            mask_cluster = np.ones((3, 3, 3))

            if nneigh == 7:
                mask_cluster[0, 0, 0] = 0
                mask_cluster[0, 1, 0] = 0
                mask_cluster[0, 2, 0] = 0
                mask_cluster[0, 0, 1] = 0
                mask_cluster[0, 2, 1] = 0
                mask_cluster[0, 0, 2] = 0
                mask_cluster[0, 1, 2] = 0
                mask_cluster[0, 2, 2] = 0
                mask_cluster[1, 0, 0] = 0
                mask_cluster[1, 2, 0] = 0
                mask_cluster[1, 0, 2] = 0
                mask_cluster[1, 2, 2] = 0
                mask_cluster[2, 0, 0] = 0
                mask_cluster[2, 1, 0] = 0
                mask_cluster[2, 2, 0] = 0
                mask_cluster[2, 0, 1] = 0
                mask_cluster[2, 2, 1] = 0
                mask_cluster[2, 0, 2] = 0
                mask_cluster[2, 1, 2] = 0
                mask_cluster[2, 2, 2] = 0

            elif nneigh == 19:
                mask_cluster[0, 0, 0] = 0
                mask_cluster[0, 2, 0] = 0
                mask_cluster[2, 0, 0] = 0
                mask_cluster[2, 2, 0] = 0
                mask_cluster[0, 0, 2] = 0
                mask_cluster[0, 2, 2] = 0
                mask_cluster[2, 0, 2] = 0
                mask_cluster[2, 2, 2] = 0

        elif nneigh == 125:
            mask_cluster = np.ones((5, 5, 5))

        # Exclude voxels outside the mask from every neighbourhood
        ranks_niimg_data[~logical_mask] = 0
        tied_rank_corrections[~logical_mask] = 0
        # Sum over the neighbourhood of every voxel: number of voxels in the
        # mask, ranks per timepoint and tied rank corrections; at the edges
        # of the volume, only the neighbours within it are used
        n_neighbours = sp.ndimage.correlate(
            logical_mask.astype(np.float64),
            mask_cluster,
            mode="constant",
        )
        neighbourhood_rank_sums = sp.ndimage.correlate(
            ranks_niimg_data,
            mask_cluster[..., np.newaxis],
            mode="constant",
        )
        del ranks_niimg_data
        neighbourhood_tied_rank_corrections = sp.ndimage.correlate(
            tied_rank_corrections,
            mask_cluster,
            mode="constant",
        )
        # Calculate Kendall's coefficient of concordance (KCC)
        np.square(neighbourhood_rank_sums, out=neighbourhood_rank_sums)
        numerator = (12 * np.sum(neighbourhood_rank_sums, axis=-1)) - (
            3 * n_neighbours**2 * n_t * (n_t + 1) ** 2
        )
        del neighbourhood_rank_sums
        denominator = (n_neighbours**2 * n_t * (n_t**2 - 1)) - (
            n_neighbours * neighbourhood_tied_rank_corrections
        )
        # If all the time series in the neighbourhood are fully tied, the
        # denominator is 0 and KCC is set to 0, same as AFNI's 3dReHo
        with np.errstate(divide="ignore", invalid="ignore"):
            kcc = np.where(denominator == 0, 0.0, numerator / denominator)

        # Initialize 3D array to store reho map; voxels outside the mask stay
        # at 0, same as AFNI's 3dReHo
        reho_map = np.zeros((n_x, n_y, n_z), dtype=np.float32)
        reho_map[logical_mask] = kcc[logical_mask]

        # Create new image like target image
        output_data = nimg.new_img_like(
            ref_niimg=niimg,
            data=reho_map,
            copy_header=False,
        )

        # Create element-scoped tempdir so that the ReHo map is
        # available later as nibabel stores file path reference for
        # loading on computation
        element_tempdir = WorkDirManager().get_element_tempdir(
            prefix="junifer_reho"
        )
        output_path = element_tempdir / "output.nii.gz"
        # Save computed data to file
        nib.save(output_data, output_path)

        return output_data, output_path  # type: ignore


def _rank_with_ties(data: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Rank data along the last axis and compute tied rank corrections.

    Equivalent to ``scipy.stats.rankdata(data, axis=-1)`` (tied values get
    their average rank and NaN propagates to the whole time series), but
    sorting only once.

    Parameters
    ----------
    data : numpy.ndarray
        The data to rank along the last axis.

    Returns
    -------
    numpy.ndarray
        The ranks of ``data`` along the last axis.
    numpy.ndarray
        The tied rank correction, the sum of ``t^3 - t`` over the groups of
        ``t`` tied values, for every element along the last axis.

    """
    n = data.shape[-1]
    sort_idx = np.argsort(data, axis=-1, kind="stable")
    sorted_data = np.take_along_axis(data, sort_idx, axis=-1)
    positions = np.arange(1, n + 1)
    # Mark the first and last sample of every tie group in sorted order
    is_first = np.ones(data.shape, dtype=bool)
    is_first[..., 1:] = sorted_data[..., 1:] != sorted_data[..., :-1]
    del sorted_data
    is_last = np.ones(data.shape, dtype=bool)
    is_last[..., :-1] = is_first[..., 1:]
    # Min and max rank of the tie group of every sample in sorted order
    min_ranks = np.maximum.accumulate(
        np.where(is_first, positions, 0), axis=-1
    )
    del is_first
    max_ranks = np.flip(
        np.minimum.accumulate(
            np.flip(np.where(is_last, positions, n + 1), axis=-1), axis=-1
        ),
        axis=-1,
    )
    del is_last
    # Every sample belongs to a tie group of size t = max - min + 1, and
    # summing t^2 - 1 over the samples is the same as summing t^3 - t over
    # the tie groups
    tie_sizes = max_ranks - min_ranks + 1
    tied_rank_corrections = np.sum(tie_sizes**2 - 1, axis=-1).astype(
        np.float64
    )
    del tie_sizes
    # Tied values get their average rank; put back in the original order
    ranks = np.empty(data.shape, dtype=np.float64)
    np.put_along_axis(ranks, sort_idx, (min_ranks + max_ranks) / 2, axis=-1)
    # Propagate NaN to the whole time series, same as scipy.stats.rankdata
    has_nan = np.isnan(data).any(axis=-1)
    ranks[has_nan] = np.nan
    tied_rank_corrections[has_nan] = np.nan
    return ranks, tied_rank_corrections
