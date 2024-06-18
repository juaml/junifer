"""Provide class for computing ALFF using AFNI."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from functools import lru_cache
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    ClassVar,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)

import nibabel as nib

from ...pipeline import WorkDirManager
from ...pipeline.singleton import singleton
from ...utils import logger, run_ext_cmd


if TYPE_CHECKING:
    from nibabel import Nifti1Image


__all__ = ["AFNIALFF"]


@singleton
class AFNIALFF:
    """Class for computing ALFF using AFNI.

    This class uses AFNI's 3dRSFC to compute ALFF. It's designed as a singleton
    with caching for efficient computation.

    """

    _EXT_DEPENDENCIES: ClassVar[List[Dict[str, Union[str, List[str]]]]] = [
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
        data: "Nifti1Image",
        highpass: float,
        lowpass: float,
        tr: Optional[float],
    ) -> Tuple["Nifti1Image", "Nifti1Image", Path, Path]:
        """Compute ALFF + fALFF map.

        Parameters
        ----------
        data : 4D Niimg-like object
            Images to process.
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

        # Create component-scoped tempdir
        tempdir = WorkDirManager().get_tempdir(prefix="afni_alff+falff")

        # Save target data to a component-scoped tempfile
        nifti_in_file_path = tempdir / "input.nii"  # needs to be .nii
        nib.save(data, nifti_in_file_path)

        # Set 3dRSFC command
        alff_falff_out_path_prefix = tempdir / "alff_falff"
        bp_cmd = [
            "3dRSFC",
            f"-prefix {alff_falff_out_path_prefix.resolve()}",
            f"-input {nifti_in_file_path.resolve()}",
            f"-band {highpass} {lowpass}",
            "-no_rsfa -nosat -nodetrend",
        ]
        # Check tr
        if tr is not None:
            bp_cmd.append(f"-dt {tr}")
        # Call 3dRSFC
        run_ext_cmd(name="3dRSFC", cmd=bp_cmd)

        # Create element-scoped tempdir so that the ALFF and fALFF maps are
        # available later as nibabel stores file path reference for
        # loading on computation
        element_tempdir = WorkDirManager().get_element_tempdir(
            prefix="afni_alff_falff"
        )

        params_suffix = f"_{highpass}_{lowpass}_{tr}"

        # Convert alff afni to nifti
        alff_afni_to_nifti_out_path = (
            element_tempdir / f"alff{params_suffix}_output.nii"
        )  # needs to be .nii
        convert_alff_cmd = [
            "3dAFNItoNIFTI",
            f"-prefix {alff_afni_to_nifti_out_path.resolve()}",
            f"{alff_falff_out_path_prefix}_ALFF+orig.BRIK",
        ]
        # Call 3dAFNItoNIFTI
        run_ext_cmd(name="3dAFNItoNIFTI", cmd=convert_alff_cmd)

        # Convert falff afni to nifti
        falff_afni_to_nifti_out_path = (
            element_tempdir / f"falff{params_suffix}_output.nii"
        )  # needs to be .nii
        convert_falff_cmd = [
            "3dAFNItoNIFTI",
            f"-prefix {falff_afni_to_nifti_out_path.resolve()}",
            f"{alff_falff_out_path_prefix}_fALFF+orig.BRIK",
        ]
        # Call 3dAFNItoNIFTI
        run_ext_cmd(name="3dAFNItoNIFTI", cmd=convert_falff_cmd)

        # Load nifti
        alff_data = nib.load(alff_afni_to_nifti_out_path)
        falff_data = nib.load(falff_afni_to_nifti_out_path)

        # Delete tempdir
        WorkDirManager().delete_tempdir(tempdir)

        return (
            alff_data,
            falff_data,
            alff_afni_to_nifti_out_path,
            falff_afni_to_nifti_out_path,
        )  # type: ignore
