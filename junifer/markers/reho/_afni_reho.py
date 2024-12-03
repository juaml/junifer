"""Provide class for computing regional homogeneity (ReHo) using AFNI."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from functools import lru_cache
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    ClassVar,
    Optional,
)

import nibabel as nib

from ...pipeline import WorkDirManager
from ...typing import ExternalDependencies
from ...utils import logger, run_ext_cmd
from ...utils.singleton import Singleton


if TYPE_CHECKING:
    from nibabel.nifti1 import Nifti1Image


__all__ = ["AFNIReHo"]


class AFNIReHo(metaclass=Singleton):
    """Class for computing ReHo using AFNI.

    This class uses AFNI's 3dReHo to compute ReHo. It's designed as a singleton
    with caching for efficient computation.

    """

    _EXT_DEPENDENCIES: ClassVar[ExternalDependencies] = [
        {
            "name": "afni",
            "commands": ["3dReHo", "3dAFNItoNIFTI"],
        },
    ]

    def __del__(self) -> None:
        """Terminate the class."""
        # Clear the computation cache
        logger.debug("Clearing cache for ReHo computation via AFNI")
        self.compute.cache_clear()

    @lru_cache(maxsize=None, typed=True)
    def compute(
        self,
        input_path: Path,
        nneigh: int = 27,
        neigh_rad: Optional[float] = None,
        neigh_x: Optional[float] = None,
        neigh_y: Optional[float] = None,
        neigh_z: Optional[float] = None,
        box_rad: Optional[int] = None,
        box_x: Optional[int] = None,
        box_y: Optional[int] = None,
        box_z: Optional[int] = None,
    ) -> tuple["Nifti1Image", Path]:
        """Compute ReHo map.

        Parameters
        ----------
        input_path : pathlib.Path
            Path to the input data.
        nneigh : {7, 19, 27}, optional
            Number of voxels in the neighbourhood, inclusive. Can be:

            * 7 : for facewise neighbours only
            * 19 : for face- and edge-wise neighbours
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
            The ReHo map as NIfTI.
        pathlib.Path
            The path to the ReHo map as NIfTI.

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
        logger.debug("Creating cache for ReHo computation via AFNI")

        # Create element-scoped tempdir
        element_tempdir = WorkDirManager().get_element_tempdir(
            prefix="afni_reho"
        )

        # Set 3dReHo command
        reho_out_path_prefix = element_tempdir / "output"
        reho_cmd = [
            "3dReHo",
            f"-prefix {reho_out_path_prefix.resolve()}",
            f"-inset {input_path.resolve()}",
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
        run_ext_cmd(name="3dReHo", cmd=reho_cmd)

        # Read header to get output suffix
        niimg = nib.load(input_path)
        header = niimg.header
        sform_code = header.get_sform(coded=True)[1]
        if sform_code == 4:
            output_suffix = "tlrc"
        else:
            output_suffix = "orig"

        # Convert afni to nifti
        reho_nifti_out_path = (
            element_tempdir / "output.nii"  # needs to be .nii
        )
        convert_cmd = [
            "3dAFNItoNIFTI",
            f"-prefix {reho_nifti_out_path.resolve()}",
            f"{reho_out_path_prefix}+{output_suffix}.BRIK",
        ]
        # Call 3dAFNItoNIFTI
        run_ext_cmd(name="3dAFNItoNIFTI", cmd=convert_cmd)

        # Load nifti
        output_data = nib.load(reho_nifti_out_path)

        return output_data, reho_nifti_out_path
