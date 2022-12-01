"""Provide estimator class for regional homogeneity (ReHo)."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
#          Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL


import shutil
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

import nibabel as nib
import numpy as np

from ...stats import kendall_w
from ...utils import logger, raise_error
from ..utils import singleton


if TYPE_CHECKING:
    from nibabel import Nifti1Image, Nifti2Image
    from nibabel.imageclasses import PARRECImage


@singleton
class ReHoEstimator:
    """Estimator class for regional homogeneity.

    This class is a singleton and is used for efficient computation of ReHo,
    by caching the ReHo map for a given set of file path and computation
    parameters.

    .. warning:: This class can only be used via ReHoBase() and is a deliberate
                 decision as it serves a specific purpose.

    Parameters
    ----------
    use_afni : bool
        Whether to use afni or not.

    """

    def __init__(self, use_afni: bool) -> None:
        self.use_afni = use_afni
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
        data: Union["Nifti1Image", "Nifti2Image"],
        nneigh: int = 27,
        neigh_rad: Optional[float] = None,
        neigh_x: Optional[float] = None,
        neigh_y: Optional[float] = None,
        neigh_z: Optional[float] = None,
        box_rad: Optional[int] = None,
        box_x: Optional[int] = None,
        box_y: Optional[int] = None,
        box_z: Optional[int] = None,
    ) -> "PARRECImage":
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
            If the 3dReHo command fails due to some issue

        Notes
        -----
        For more information on the publication, please check [1]_ , and for
        3dReHo help check:
        https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dReHo.html

        Please note that that you cannot mix `box_*` and `neigh_*` arguments.
        The arguments are prioritized by their order in the function signature.

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
        logger.info(f"3dReHo command to be executed: {reho_cmd}")
        reho_process = subprocess.run(
            reho_cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.STDOUT,
            stderr=subprocess.STDOUT,
            shell=True,
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

        # Convert afni to nifti
        reho_afni_to_nifti_out_path_prefix = self.temp_dir_path / "output"
        convert_cmd: List[str] = [
            "3dAFNItoNIFTI",
            f"-prefix {reho_afni_to_nifti_out_path_prefix.resolve()}",
            f"{reho_afni_out_path_prefix}+tlrc.BRIK",
        ]
        # Call 3dAFNItoNIFTI
        logger.info(f"3dAFNItoNIFTI command to be executed: {convert_cmd}")
        convert_process = subprocess.run(
            convert_cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.STDOUT,
            stderr=subprocess.STDOUT,
            shell=True,
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

        # Load nifti
        output_data = nib.load(f"{reho_afni_to_nifti_out_path_prefix}.nii")
        return output_data

    def _compute_reho_python(
        self,
        data: Union["Nifti1Image", "Nifti2Image"],
        nneigh: int = 27,
    ) -> "Nifti1Image":
        """Compute ReHo map.

        The implementation is borrowed from [1]_ and is released under GPLv3.
        For more information, please check there.

        Parameters
        ----------
        data : 4D Niimg-like object
            Images to process.
        nneigh : {7, 19, 27}, optional
            Number of voxels in the neighbourhood, inclusive. Can be:

            * 7 : for facewise neighbours only
            * 19 : for face- and edge-wise nieghbours
            * 27 : for face-, edge-, and node-wise neighbors

        Returns
        -------
        Niimg-like object

        Raises
        ------
        ValueError
            If `nneigh` is invalid.

        References
        ----------
        .. [1] https://github.com/FCP-INDI/C-PAC/blob/main/CPAC/reho/utils.py

        """
        valid_nneigh = (7, 19, 27)
        if nneigh not in valid_nneigh:
            raise_error(
                f"Invalid value for `nneigh`, should be one of {valid_nneigh}."
            )

        CUTNUMBER = 10

        res_data = data.get_data()

        (n_x, n_y, n_z, n_t) = res_data.shape

        # "flatten" each volume of the timeseries into one big array instead of
        # x,y,z - produces (timepoints, N voxels) shaped data array
        reshaped_res_data = np.reshape(
            res_data, (n_x * n_y * n_z, n_t), order="F"
        ).T

        # create a blank array of zeroes of size n_voxels, one for each time
        # point
        ranks_res_data = np.tile(
            np.zeros((1, reshaped_res_data.shape[1])),
            (reshaped_res_data.shape[0], 1),
        )

        # divide the number of total voxels by the cutnumber (set to 10)
        # ex. end up with a number in the thousands if there are tens of
        # thousands of voxels
        segment_length = np.ceil(
            float(reshaped_res_data.shape[1]) / float(CUTNUMBER)
        )

        for icut in range(0, CUTNUMBER):

            segment = None

            # create a Numpy array of evenly spaced values from the segment
            # starting point up until the segment_length integer
            if not (icut == (CUTNUMBER - 1)):
                segment = np.arange(
                    icut * segment_length, (icut + 1) * segment_length
                )
            else:
                segment = np.arange(
                    icut * segment_length, reshaped_res_data.shape[1]
                )

            segment = np.int64(segment[np.newaxis])

            # res_data_piece is a chunk of the original timeseries in_file, but
            # aligned with the current segment index spacing
            res_data_piece = reshaped_res_data[:, segment[0]]
            nvoxels_piece = res_data_piece.shape[1]

            # run a merge sort across the time axis, re-ordering the flattened
            # volume voxel arrays
            res_data_sorted = np.sort(res_data_piece, 0, kind="mergesort")
            sort_index = np.argsort(res_data_piece, axis=0, kind="mergesort")

            # subtract each volume from each other
            db = np.diff(res_data_sorted, 1, 0)

            # convert any zero voxels into "True" flag
            db = db == 0

            # return an n_voxel (n voxels within the current segment) sized
            # array of values, each value being the sum total of TRUE values
            # in "db"
            sumdb = np.sum(db, 0)

            temp_array = np.arange(0, n_t)
            temp_array = temp_array[:, np.newaxis]

            sorted_ranks = np.tile(temp_array, (1, nvoxels_piece))

            if np.any(sumdb[:]):

                tie_adjust_index = np.flatnonzero(sumdb)

                for i in range(0, len(tie_adjust_index)):

                    ranks = sorted_ranks[:, tie_adjust_index[i]]

                    ties = db[:, tie_adjust_index[i]]

                    tieloc = np.append(np.flatnonzero(ties), n_t + 2)
                    maxties = len(tieloc)
                    tiecount = 0

                    while tiecount < maxties - 1:
                        tiestart = tieloc[tiecount]
                        ntied = 2
                        while tieloc[tiecount + 1] == (tieloc[tiecount] + 1):
                            tiecount += 1
                            ntied += 1

                        ranks[tiestart : tiestart + ntied] = np.ceil(
                            np.float32(
                                np.sum(ranks[tiestart : tiestart + ntied])
                            )
                            / np.float32(ntied)
                        )
                        tiecount += 1

                    sorted_ranks[:, tie_adjust_index[i]] = ranks

            del db, sumdb
            sort_index_base = np.tile(
                np.multiply(np.arange(0, nvoxels_piece), n_t), [n_t, 1]
            )
            sort_index += sort_index_base
            del sort_index_base

            ranks_piece = np.zeros((n_t, nvoxels_piece))

            ranks_piece = ranks_piece.flatten(order="F")
            sort_index = sort_index.flatten(order="F")
            sorted_ranks = sorted_ranks.flatten(order="F")

            ranks_piece[sort_index] = np.array(sorted_ranks)

            ranks_piece = np.reshape(
                ranks_piece, (n_t, nvoxels_piece), order="F"
            )

            del sort_index, sorted_ranks

            ranks_res_data[:, segment[0]] = ranks_piece

        ranks_res_data = np.reshape(
            ranks_res_data, (n_t, n_x, n_y, n_z), order="F"
        )

        K = np.zeros((n_x, n_y, n_z))

        mask_cluster = np.ones((3, 3, 3))

        if nneigh == 19:
            mask_cluster[0, 0, 0] = 0
            mask_cluster[0, 2, 0] = 0
            mask_cluster[2, 0, 0] = 0
            mask_cluster[2, 2, 0] = 0
            mask_cluster[0, 0, 2] = 0
            mask_cluster[0, 2, 2] = 0
            mask_cluster[2, 0, 2] = 0
            mask_cluster[2, 2, 2] = 0

        elif nneigh == 7:

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

        for i in range(1, n_x - 1):
            for j in range(1, n_y - 1):
                for k in range(1, n_z - 1):

                    block = ranks_res_data[
                        :, i - 1 : i + 2, j - 1 : j + 2, k - 1 : k + 2
                    ]
                    mask_block = mask_cluster

                    if not (int(mask_block[1, 1, 1]) == 0):

                        if nneigh == 19 or nneigh == 7:
                            mask_block = np.multiply(mask_block, mask_cluster)

                        R_block = np.reshape(
                            block, (block.shape[0], 27), order="F"
                        )
                        mask_R_block = R_block[
                            :,
                            np.argwhere(
                                np.reshape(mask_block, (1, 27), order="F") > 0
                            )[:, 1],
                        ]

                        K[i, j, k] = kendall_w(mask_R_block, axis=1)

        output = nib.Nifti1Image(K, header=data.header, affine=data.affine)
        return output

    @lru_cache(maxsize=None, typed=True)
    def _compute(
        self,
        data: Union["Nifti1Image", "Nifti2Image"],
        **reho_params: Any,
    ) -> "PARRECImage":
        """Compute the ReHo map with memoization.

        Parameters
        ----------
        data : 4D Niimg-like object
            Images to process.
        **reho_params : dict
            Extra keyword arguments for ReHo.

        Returns
        -------
        Niimg-like object

        """
        if self.use_afni:
            output = self._compute_reho_afni(data, **reho_params)
        else:
            output = self._compute_reho_python(data, **reho_params)
        return output

    def fit_transform(
        self, input_data: Dict[str, Any], **reho_params: Any
    ) -> "PARRECImage":
        """Fit and transform for the estimator.

        Parameters
        ----------
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
            # Clear the cache
            self._compute.cache_clear()
            # Clear temporary directory files
            for file_ in self.temp_dir_path.iterdir():
                file_.unlink(missing_ok=True)
            # Set the new file path
            self._file_path = bold_path
        # Compute
        return self._compute(bold_data, **reho_params)
