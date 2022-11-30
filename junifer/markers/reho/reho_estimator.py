"""Provide estimator class for regional homogeneity (ReHo)."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
#          Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL


import subprocess
import tempfile
import shutil
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

import nibabel as nib

from ...utils import logger, raise_error
from ..utils import singleton


if TYPE_CHECKING:
    from nibabel import Nifti1Image, Nifti2Image
    from nibabel.imageclasses import PARRECImage

@singleton
def ReHoEstimator():
    """Estimator class for regional homogeneity.

    This class is a singleton and is used for efficient computation of ReHo,
    by caching the ReHo map for a given set of file path and computation
    parameters.

    .. warning:: This class can only be used via ReHoBase() and is a deliberate
                 decision as it serves a specific purpose.

    """

    def __init__(self):
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

            * 7 : for facewise neighours only
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
               Brain connectivity, Volumne 3(5), Pages 523-35.
               https://doi.org/10.1089/brain.2013.0154

        """
        # Save niimg to nii.gz
        nifti_in_file_path = self.temp_dir_path / "input.nii"
        nib.save(data, nifti_in_file_path)

        # Set 3dReHo command
        reho_afni_out_path_prefix = self.temp_dir_path / "reho"
        reho_cmd: List[str] = ["3dReHo", f"-prefix {reho_afni_out_path_prefix.resolve()}", f"-inset {nifti_in_file_path.resolve()}"]
        # Check ellipsoidal / cuboidal volume arguments
        if neigh_rad:
            reho_cmd.append(f"-neigh_RAD {neigh_rad}")
        elif neigh_x and neigh_y and neigh_z:
            reho_cmd.extend(
                [f"-neigh_X {neigh_x}", f"-neigh_Y {neigh_y}", f"-neigh_Z {neigh_z}"]
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
           logger.info(f"3dReHo succeeded with the following output: {reho_process.stdout}")
        else:
            raise_error(
                msg=f"3dReHo failed with the following error: {reho_process.stdout}",
                klass=RuntimeError,
            )
        # Convert afni to nifti
        reho_afni_to_nifti_out_path_prefix = self.temp_dir_path / "output"
        convert_cmd: List[str] = ["3dAFNItoNIFTI", f"-prefix {reho_afni_to_nifti_out_path_prefix.resolve()}", f"{reho_afni_out_path_prefix}+tlrc.BRIK"]
        # Call 3dAFNItoNIFTI
        logger.info(f"3dAFNItoNIFTI command to be executed: {convert_cmd}")
        convert_process = subprocess.run(
            convert_cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
            shell=True,
            check=False,
        )
        if convert_process.returncode == 0:
            logger.info(f"3dAFNItoNIFTI succeeded with the following output: {convert_process.stdout}")
        else:
            raise_error(
                msg=f"3dAFNItoNIFTI failed with the following error: {convert_process.stdout}",
                klass=RuntimeError,
            )
        # Load nifti
        output_data = nib.load(f"{reho_afni_to_nifti_out_path_prefix}.nii")
        return output_data


    def _compute_reho_python(self):
        """Compute ReHo map."""
        ...

    @lru_cache(maxsize=None, typed=True)
    def _compute(
        self,
        data: Union["Nifti1Image", "Nifti2Image"],
        **reho_params: Any,
    ):
        """Compute the ReHo map with memoization.

        Parameters
        ----------
        data : 4D Niimg-like object
            Images to process.
        **reho_params : dict
            Extra keyword arguments for ReHo.

        Returns
        -------

        """
        if self._use_afni:
            output = self._compute_reho_afni(data, **reho_params)
        else:
            output = self._compute_reho_python(data, **reho_params)
        return output

    def fit_transform(self, input_data: Dict[str, Any], **params: Any):
        """Fit and transform for the estimator.

        Parameters
        ----------
        input_data : dict

        **params : dict

        """
        bold_path = input_data["BOLD"]["path"]
        bold_data = input_data["BOLD"]["data"]
        # Clear cache if file path is different from when caching was done
        if self._file_path != bold_path:
            # Clear the cache
            self._compute.cache_clear()
            # Set the new file path
            self._file_path = bold_path
        # Compute
        return self._compute(bold_data, **params)
