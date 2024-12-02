"""Provide class for computing regional homogeneity (ReHo) using junifer."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from functools import lru_cache
from itertools import product
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    ClassVar,
)

import nibabel as nib
import numpy as np
import scipy as sp
from nilearn import image as nimg
from nilearn import masking as nmask

from ...pipeline import WorkDirManager
from ...typing import Dependencies
from ...utils import logger, raise_error
from ...utils.singleton import Singleton


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
        niimg_data = niimg.get_fdata().copy()
        # Get scan dimensions
        n_x, n_y, n_z, _ = niimg_data.shape

        # Get rank of every voxel across time series
        ranks_niimg_data = sp.stats.rankdata(niimg_data, axis=-1)

        # Initialize 3D array to store tied rank correction for every voxel
        tied_rank_corrections = np.zeros((n_x, n_y, n_z), dtype=np.float64)
        # Calculate tied rank correction for every voxel
        for i_x, i_y, i_z in product(range(n_x), range(n_y), range(n_z)):
            # Calculate tied rank count for every voxel across time series
            _, tie_count = np.unique(
                ranks_niimg_data[i_x, i_y, i_z, :],
                return_counts=True,
            )
            # Calculate and store tied rank correction for every voxel across
            # timeseries
            tied_rank_corrections[i_x, i_y, i_z] = np.sum(
                tie_count**3 - tie_count
            )

        # Initialize 3D array to store reho map
        reho_map = np.ones((n_x, n_y, n_z), dtype=np.float32)

        # TODO(synchon): this will give incorrect results if
        # template doesn't match, hence needs to be changed
        # after #299 is merged
        # Calculate whole brain mask
        mni152_whole_brain_mask = nmask.compute_brain_mask(
            target_img=niimg,
            threshold=0.5,
            mask_type="whole-brain",
        )
        # Convert 0 / 1 array to bool
        logical_mni152_whole_brain_mask = (
            mni152_whole_brain_mask.get_fdata().astype(bool)
        )

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

            start_idx = 1
            end_idx = 2

        elif nneigh == 125:
            mask_cluster = np.ones((5, 5, 5))
            start_idx = 2
            end_idx = 3

        # Convert 0 / 1 array to bool
        logical_mask_cluster = mask_cluster.astype(bool)

        for i, j, k in product(
            range(start_idx, n_x - (end_idx - 1)),
            range(start_idx, n_y - (end_idx - 1)),
            range(start_idx, n_z - (end_idx - 1)),
        ):
            # Get mask only for neighbourhood
            logical_neighbourhood_mni152_whole_brain_mask = (
                logical_mni152_whole_brain_mask[
                    i - start_idx : i + end_idx,
                    j - start_idx : j + end_idx,
                    k - start_idx : k + end_idx,
                ]
            )
            # Perform logical AND to get neighbourhood mask;
            # done to take care of brain boundaries
            neighbourhood_mask = (
                logical_mask_cluster
                & logical_neighbourhood_mni152_whole_brain_mask
            )
            # Continue if voxel is restricted by mask
            if neighbourhood_mask[1, 1, 1] == 0:
                continue

            # Get ranks for the neighbourhood
            neighbourhood_ranks = ranks_niimg_data[
                i - start_idx : i + end_idx,
                j - start_idx : j + end_idx,
                k - start_idx : k + end_idx,
                :,
            ]
            # Get tied ranks corrections for the neighbourhood
            neighbourhood_tied_ranks_corrections = tied_rank_corrections[
                i - start_idx : i + end_idx,
                j - start_idx : j + end_idx,
                k - start_idx : k + end_idx,
            ]
            # Mask neighbourhood ranks
            masked_neighbourhood_ranks = neighbourhood_ranks[
                logical_mask_cluster, :
            ]
            # Mask tied ranks corrections for the neighbourhood
            masked_tied_rank_corrections = (
                neighbourhood_tied_ranks_corrections[logical_mask_cluster]
            )
            # Calculate KCC
            reho_map[i, j, k] = _kendall_w_reho(
                timeseries_ranks=masked_neighbourhood_ranks,
                tied_rank_corrections=masked_tied_rank_corrections,
            )

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


def _kendall_w_reho(
    timeseries_ranks: np.ndarray, tied_rank_corrections: np.ndarray
) -> float:
    """Calculate Kendall's coefficient of concordance (KCC) for ReHo map.

    ..note:: This function should only be used to calculate KCC for a ReHo map.
             For general use, check out ``junifer.stats.kendall_w``.

    Parameters
    ----------
    timeseries_ranks : 2D numpy.ndarray
        A matrix of ranks of a subset subject's brain voxels.
    tied_rank_corrections : 3D numpy.ndarray
        A 3D array consisting of the tied rank corrections for the ranks
        of a subset subject's brain voxels.

    Returns
    -------
    float
        Kendall's W (KCC) of the given timeseries matrix.

    """
    m, n = timeseries_ranks.shape  # annotators X items

    numerator = (12 * np.sum(np.square(np.sum(timeseries_ranks, axis=0)))) - (
        3 * m**2 * n * (n + 1) ** 2
    )
    denominator = (m**2 * n * (n**2 - 1)) - (m * np.sum(tied_rank_corrections))

    if denominator == 0:
        kcc = 1.0
    else:
        kcc = numerator / denominator

    return kcc
