"""Provide estimator class for regional homogeneity (ReHo)."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
#          Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL


import hashlib
import shutil
import subprocess
import tempfile
from functools import lru_cache
from itertools import product
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, cast

import nibabel as nib
import numpy as np
from nilearn import image as nimg
from nilearn import masking as nmask
from scipy.stats import rankdata

from ...utils import logger, raise_error
from ..utils import singleton


if TYPE_CHECKING:
    from nibabel import Nifti1Image


@singleton
class ReHoEstimator:
    """Estimator class for regional homogeneity.

    This class is a singleton and is used for efficient computation of ReHo,
    by caching the ReHo map for a given set of file path and computation
    parameters.

    .. warning:: This class can only be used via ReHoBase() and is a deliberate
                 decision as it serves a specific purpose.

    Attributes
    ----------
    temp_dir_path : pathlib.Path
        Path to the temporary directory for assets storage.

    """

    def __init__(self) -> None:
        self._file_path = None
        # Create temporary directory for intermittent storage of assets during
        # computation via afni's 3dReHo
        self.temp_dir_path = Path(tempfile.mkdtemp())

    def __del__(self) -> None:
        """Cleanup."""
        # Delete temporary directory and ignore errors for read-only files
        shutil.rmtree(self.temp_dir_path, ignore_errors=True)

    def _compute_reho_afni(
        self,
        data: "Nifti1Image",
        nneigh: int = 27,
        neigh_rad: Optional[float] = None,
        neigh_x: Optional[float] = None,
        neigh_y: Optional[float] = None,
        neigh_z: Optional[float] = None,
        box_rad: Optional[int] = None,
        box_x: Optional[int] = None,
        box_y: Optional[int] = None,
        box_z: Optional[int] = None,
    ) -> "Nifti1Image":
        """Compute ReHo map via afni's 3dReHo.

        Parameters
        ----------
        data : 4D Niimg-like object
            Images to process.
        nneigh : {7, 19, 27}, optional
            Number of voxels in the neighbourhood, inclusive. Can be:

            * 7 : for facewise neighbours only
            * 19 : for face- and edge-wise nieghbours
            * 27 : for face-, edge-, and node-wise neighbors

            (default 27).
        neigh_rad : positive float, optional
            The radius of a desired neighbourhood (default None).
        neigh_x : positive float, optional
            The semi-radius for x-axis of ellipsoidal volumes (default None).
        neigh_y : positive float, optional
            The semi-radius for y-axis of ellipsoidal volumes (default None).
        neigh_z : positive float, optional
            The semi-radius for z-axis of ellipsoidal volumes (default None).
        box_rad : positive int, optional
            The number of voxels outward in a given cardinal direction for a
            cubic box centered on a given voxel (default None).
        box_x : positive int, optional
            The number of voxels for +/- x-axis of cuboidal volumes
            (default None).
        box_y : positive int, optional
            The number of voxels for +/- y-axis of cuboidal volumes
            (default None).
        box_z : positive int, optional
            The number of voxels for +/- z-axis of cuboidal volumes
            (default None).

        Returns
        -------
        Niimg-like object

        Raises
        ------
        RuntimeError
            If the 3dReHo command fails due to some issue.

        Notes
        -----
        For more information on the publication, please check [1]_ , and for
        3dReHo help check:
        https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dReHo.html

        Please note that that you cannot mix ``box_*`` and ``neigh_*``
        arguments. The arguments are prioritized by their order in the function
        signature.

        As the process also depends on the conversion of AFNI files to NIFTI
        via afni's 3dAFNItoNIFTI, the help for that can be found at:
        https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dAFNItoNIFTI.html

        References
        ----------
        .. [1] Taylor, P.A., & Saad, Z.S. (2013).
               FATCAT: (An Efficient) Functional And Tractographic Connectivity
               Analysis Toolbox.
               Brain connectivity, Volume 3(5), Pages 523-35.
               https://doi.org/10.1089/brain.2013.0154

        """
        # Save niimg to nii.gz
        nifti_in_file_path = self.temp_dir_path / "input.nii"
        nib.save(data, nifti_in_file_path)

        # Set 3dReHo command
        reho_afni_out_path_prefix = self.temp_dir_path / "reho"
        reho_cmd: List[str] = [
            "3dReHo",
            f"-prefix {reho_afni_out_path_prefix.resolve()}",
            f"-inset {nifti_in_file_path.resolve()}",
        ]
        # Check ellipsoidal / cuboidal volume arguments
        if neigh_rad:
            reho_cmd.append(f"-neigh_RAD {neigh_rad}")
        elif neigh_x and neigh_y and neigh_z:
            reho_cmd.extend(
                [
                    f"-neigh_X {neigh_x}",
                    f"-neigh_Y {neigh_y}",
                    f"-neigh_Z {neigh_z}",
                ]
            )
        elif box_rad:
            reho_cmd.append(f"-box_RAD {box_rad}")
        elif box_x and box_y and box_z:
            reho_cmd.extend(
                [f"-box_X {box_x}", f"-box_Y {box_y}", f"-box_Z {box_z}"]
            )
        else:
            reho_cmd.append(f"-nneigh {nneigh}")
        # Call 3dReHo
        reho_cmd_str = " ".join(reho_cmd)
        logger.info(f"3dReHo command to be executed: {reho_cmd_str}")
        reho_process = subprocess.run(
            reho_cmd_str,  # string needed with shell=True
            stdin=subprocess.DEVNULL,
            shell=True,  # needed for respecting $PATH
            check=False,
        )
        if reho_process.returncode == 0:
            logger.info(
                "3dReHo succeeded with the following output: "
                f"{reho_process.stdout}"
            )
        else:
            raise_error(
                msg="3dReHo failed with the following error: "
                f"{reho_process.stdout}",
                klass=RuntimeError,
            )

        # SHA256 for bypassing memmap
        sha256_params = hashlib.sha256(bytes(reho_cmd_str, "utf-8"))
        # Convert afni to nifti
        reho_afni_to_nifti_out_path = (
            self.temp_dir_path / f"output_{sha256_params.hexdigest()}.nii"
        )
        convert_cmd: List[str] = [
            "3dAFNItoNIFTI",
            f"-prefix {reho_afni_to_nifti_out_path.resolve()}",
            f"{reho_afni_out_path_prefix}+tlrc.BRIK",
        ]
        # Call 3dAFNItoNIFTI
        convert_cmd_str = " ".join(convert_cmd)
        logger.info(f"3dAFNItoNIFTI command to be executed: {convert_cmd_str}")
        convert_process = subprocess.run(
            convert_cmd_str,  # string needed with shell=True
            stdin=subprocess.DEVNULL,
            shell=True,  # needed for respecting $PATH
            check=False,
        )
        if convert_process.returncode == 0:
            logger.info(
                "3dAFNItoNIFTI succeeded with the following output: "
                f"{convert_process.stdout}"
            )
        else:
            raise_error(
                msg="3dAFNItoNIFTI failed with the following error: "
                f"{convert_process.stdout}",
                klass=RuntimeError,
            )

        # Cleanup intermediate files
        for fname in self.temp_dir_path.glob("reho*"):
            fname.unlink()

        # Load nifti
        output_data = nib.load(reho_afni_to_nifti_out_path)
        # Stupid casting
        output_data = cast("Nifti1Image", output_data)
        return output_data

    def _compute_reho_python(
        self,
        data: "Nifti1Image",
        nneigh: int = 27,
    ) -> "Nifti1Image":
        """Compute ReHo map.

        Parameters
        ----------
        data : 4D Niimg-like object
            Images to process.
        nneigh : {7, 19, 27, 125}, optional
            Number of voxels in the neighbourhood, inclusive. Can be:

            * 7 : for facewise neighbours only
            * 19 : for face- and edge-wise nieghbours
            * 27 : for face-, edge-, and node-wise neighbors
            * 125 : for 5x5 cuboidal volume

            (default 27).
        Returns
        -------
        Niimg-like object

        Raises
        ------
        ValueError
            If ``nneigh`` is invalid.

        """
        valid_nneigh = (7, 19, 27, 125)
        if nneigh not in valid_nneigh:
            raise_error(
                f"Invalid value for `nneigh`, should be one of {valid_nneigh}."
            )

        logger.info(f"Computing ReHo map using {nneigh} neighbours.")
        # Get scan data
        niimg_data = data.get_fdata()
        # Get scan dimensions
        n_x, n_y, n_z, _ = niimg_data.shape

        # Get rank of every voxel across time series
        ranks_niimg_data = rankdata(niimg_data, axis=-1)

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

        # Calculate whole brain mask
        mni152_whole_brain_mask = nmask.compute_brain_mask(
            data, threshold=0.5, mask_type="whole-brain"
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

        output = nimg.new_img_like(data, reho_map, copy_header=False)
        return output

    @lru_cache(maxsize=None, typed=True)
    def _compute(
        self,
        use_afni: bool,
        data: "Nifti1Image",
        **reho_params: Any,
    ) -> "Nifti1Image":
        """Compute the ReHo map with memoization.

        Parameters
        ----------
        use_afni : bool
            Whether to use afni or not.
        data : 4D Niimg-like object
            Images to process.
        **reho_params : dict
            Extra keyword arguments for ReHo.

        Returns
        -------
        Niimg-like object

        """
        if use_afni:
            output = self._compute_reho_afni(data, **reho_params)
        else:
            output = self._compute_reho_python(data, **reho_params)
        return output

    def fit_transform(
        self,
        use_afni: bool,
        input_data: Dict[str, Any],
        **reho_params: Any,
    ) -> "Nifti1Image":
        """Fit and transform for the estimator.

        Parameters
        ----------
        use_afni : bool
            Whether to use afni or not.
        input_data : dict
            The BOLD data as dictionary.
        **reho_params : dict
            Extra keyword arguments for ReHo.

        Returns
        -------
        Niimg-like object

        """
        bold_path = input_data["path"]
        bold_data = input_data["data"]
        # Clear cache if file path is different from when caching was done
        if self._file_path != bold_path:
            logger.info(f"Removing ReHo map cache at {self._file_path}.")
            # Clear the cache
            self._compute.cache_clear()
            # Clear temporary directory files
            for file_ in self.temp_dir_path.iterdir():
                file_.unlink(missing_ok=True)
            # Set the new file path
            self._file_path = bold_path
        else:
            logger.info(f"Using ReHo map cache at {self._file_path}.")
        # Compute
        return self._compute(use_afni, bold_data, **reho_params)


def _kendall_w_reho(
    timeseries_ranks: np.ndarray, tied_rank_corrections: np.ndarray
) -> float:
    """Calculate Kendall's coefficient of concordance (KCC) for ReHo map.

    ..note:: This function should only be used to calculate KCC for a ReHo map.
             For general use, check out ``junifer.stats.kendall_w``.

    Parameters
    ----------
    timeseries_matrix : 2D numpy.ndarray
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
    denominator = (m**2 * n * (n**2 - 1)) - (
        m * np.sum(tied_rank_corrections)
    )

    if denominator == 0:
        kcc = 1.0
    else:
        kcc = numerator / denominator

    return kcc
