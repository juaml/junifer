"""Provide class for computing ALFF using AFNI."""

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


__all__ = ["AFNIALFF"]


class AFNIALFF(metaclass=Singleton):
    """Class for computing ALFF using AFNI.

    This class uses AFNI's 3dRSFC to compute ALFF. It's designed as a singleton
    with caching for efficient computation.

    """

    _EXT_DEPENDENCIES: ClassVar[ExternalDependencies] = [
        {
            "name": "afni",
            "commands": ["3dRSFC", "3dAFNItoNIFTI"],
        },
    ]

    def __del__(self) -> None:
        """Terminate the class."""
        # Clear the computation cache
        logger.debug("Clearing cache for ALFF computation via AFNI")
        self.compute.cache_clear()

    @lru_cache(maxsize=None, typed=True)
    def compute(
        self,
        input_path: Path,
        highpass: float,
        lowpass: float,
        tr: Optional[float],
    ) -> tuple["Nifti1Image", "Nifti1Image", Path, Path]:
        """Compute ALFF + fALFF map.

        Parameters
        ----------
        input_path : pathlib.Path
            Path to the input data.
        highpass : positive float
            Highpass cutoff frequency.
        lowpass : positive float
            Lowpass cutoff frequency.
        tr : positive float, optional
            The Repetition Time of the BOLD data.

        Returns
        -------
        Niimg-like object
            ALFF map.
        Niimg-like object
            fALFF map.
        pathlib.Path
            The path to the ALFF map as NIfTI.
        pathlib.Path
            The path to the fALFF map as NIfTI.

        """
        logger.debug("Creating cache for ALFF computation via AFNI")

        # Create element-scoped tempdir
        element_tempdir = WorkDirManager().get_element_tempdir(
            prefix="afni_lff"
        )

        # Set 3dRSFC command
        lff_out_path_prefix = element_tempdir / "output"
        bp_cmd = [
            "3dRSFC",
            f"-prefix {lff_out_path_prefix.resolve()}",
            f"-input {input_path.resolve()}",
            f"-band {highpass} {lowpass}",
            "-no_rsfa -nosat -nodetrend",
        ]
        # Check tr
        if tr is not None:
            bp_cmd.append(f"-dt {tr}")
        # Call 3dRSFC
        run_ext_cmd(name="3dRSFC", cmd=bp_cmd)

        # Read header to get output suffix
        niimg = nib.load(input_path)
        header = niimg.header
        sform_code = header.get_sform(coded=True)[1]
        if sform_code == 4:
            output_suffix = "tlrc"
        else:
            output_suffix = "orig"
        # Set params suffix
        params_suffix = f"_{highpass}_{lowpass}_{tr}"

        # Convert alff afni to nifti
        alff_nifti_out_path = (
            element_tempdir / f"output_alff{params_suffix}.nii"
        )  # needs to be .nii
        convert_alff_cmd = [
            "3dAFNItoNIFTI",
            f"-prefix {alff_nifti_out_path.resolve()}",
            f"{lff_out_path_prefix}_ALFF+{output_suffix}.BRIK",
        ]
        # Call 3dAFNItoNIFTI
        run_ext_cmd(name="3dAFNItoNIFTI", cmd=convert_alff_cmd)

        # Convert falff afni to nifti
        falff_nifti_out_path = (
            element_tempdir / f"output_falff{params_suffix}.nii"
        )  # needs to be .nii
        convert_falff_cmd = [
            "3dAFNItoNIFTI",
            f"-prefix {falff_nifti_out_path.resolve()}",
            f"{lff_out_path_prefix}_fALFF+{output_suffix}.BRIK",
        ]
        # Call 3dAFNItoNIFTI
        run_ext_cmd(name="3dAFNItoNIFTI", cmd=convert_falff_cmd)

        # Load nifti
        alff_data = nib.load(alff_nifti_out_path)
        falff_data = nib.load(falff_nifti_out_path)

        return (
            alff_data,
            falff_data,
            alff_nifti_out_path,
            falff_nifti_out_path,
        )
