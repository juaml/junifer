"""Provide estimator class for regional homogeneity (ReHo)."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
#          Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from typing import TYPE_CHECKING, Any, Dict, Tuple, Union, Optional

import shutil
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path

import nibabel as nib
import numpy as np
from scipy import signal

from nilearn import image as nimg

from ...utils import logger, raise_error
from ..utils import singleton


if TYPE_CHECKING:
    from nibabel import Nifti1Image, Nifti2Image


@singleton
class AmplitudeLowFrequencyFluctuationEstimator:
    """Estimator class for AmplitudeLowFrequencyFluctuationBase.

    This class is a singleton and is used for efficient computation of fALFF,
    by caching the voxel-wise ALFF map for a given set of file path and
    computation parameters.

    .. warning:: This class can only be used via
    :class:`junifer.markers.falff.AmplitudeLowFrequencyFluctuationBase`
    as it serves a specific purpose.

    Parameters
    ----------
    use_afni : bool
        Whether to use afni for computation. If False, will use python.

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

    @staticmethod
    def _run_afni_cmd(cmd: str) -> None:
        """Run AFNI command.

        Parameters
        ----------
        cmd : str
            AFNI command to be executed.

        Raises
        ------
        RuntimeError
            If AFNI command fails.
        """
        logger.info(f"AFNI command to be executed: {cmd}")
        process = subprocess.run(
            cmd,
            stdin=subprocess.DEVNULL,
            # stdout=subprocess.STDOUT,
            # stderr=subprocess.STDOUT,
            shell=True,
            check=False,
        )
        if process.returncode == 0:
            logger.info(
                "AFNI command succeeded with the following output: "
                f"{process.stdout}"
            )
        else:
            raise_error(
                msg="AFNI command failed with the following error: "
                f"{process.stdout}",
                klass=RuntimeError,
            )

    def _compute_alff_afni(
        self,
        data: Union["Nifti1Image", "Nifti2Image"],
        highpass: float,
        lowpass: float,
        tr: Optional[float],
    ) -> Tuple["Nifti1Image", "Nifti1Image"]:
        """Compute ALFF map via afni's commands.

        Parameters
        ----------
        data : 4D Niimg-like object
            Images to process.
        highpass : float
            Highpass cutoff frequency.
        lowpass : float
            Lowpass cutoff frequency.
        tr : float, optional
            The Repetition Time of the BOLD data.

        Returns
        -------
        alff: Niimg-like object
            ALFF map.
        falff: Niimg-like object
            fALFF map.

        Raises
        ------
        RuntimeError
            If the AFNI commands fails due to some issues

        """

        # Save niimg to nii.gz
        nifti_in_file_path = self.temp_dir_path / "input.nii"
        nib.save(data, nifti_in_file_path)

        # Bandpass the data
        falff_afni_out_path_prefix = self.temp_dir_path / "temp_falff"

        bp_cmd = (
            "3dRSFC "
            f"-prefix {falff_afni_out_path_prefix.resolve()} "
            f"-input {nifti_in_file_path.resolve()} "
            f"-band {highpass} {lowpass} "
            "-no_rsfa  "
        )
        if tr is not None:
            bp_cmd += f"-dt {tr} "
        self._run_afni_cmd(bp_cmd)

        params_suffix = f"_{highpass}_{lowpass}_{tr}"

        alff_fname = self.temp_dir_path / f"alff{params_suffix}.nii"

        convert_cmd = (
            "3dAFNItoNIFTI "
            f"-prefix {alff_fname.resolve()} "
            f"{falff_afni_out_path_prefix}_ALFF+tlrc.BRIK "
        )
        self._run_afni_cmd(convert_cmd)

        falff_fname = self.temp_dir_path / f"falff{params_suffix}.nii"

        convert_cmd = (
            "3dAFNItoNIFTI "
            f"-prefix {falff_fname.resolve()} "
            f"{falff_afni_out_path_prefix}_fALFF+tlrc.BRIK "
        )
        self._run_afni_cmd(convert_cmd)

        # Cleanup intermediate files
        for fname in self.temp_dir_path.glob("temp_falff*"):
            fname.unlink()

        # Load niftis
        alff_img = nib.load(alff_fname)
        falff_img = nib.load(falff_fname)

        return alff_img, falff_img

    def _compute_alff_python(
        self,
        data: Union["Nifti1Image", "Nifti2Image"],
        highpass: float,
        lowpass: float,
        order: int,
        tr: Optional[float],
    ) -> Tuple["Nifti1Image", "Nifti1Image"]:
        """Compute (f)ALFF map.

        Parameters
        ----------
        data : 4D Niimg-like object
            Images to process.
        highpass : float
            Highpass cutoff frequency.
        lowpass : float
            Lowpass cutoff frequency.
        order : int
            Order of the filter.
        tr : float, optional
            The Repetition Time of the BOLD data.

        Returns
        -------
        alff: Niimg-like object
            ALFF map.
        falff: Niimg-like object
            fALFF map.
        """
        timeseries = data.get_fdata()
        tr = tr or data.header["pixdim"][4]  # type: ignore
        # bandpass the data within the lowpass and highpass cutoff freqs
        Nq = 1 / (2 * tr)
        Wn = np.array([highpass / Nq, lowpass / Nq])

        b, a = signal.butter(N=order, Wn=Wn, btype="bandpass")
        ts_filt = signal.filtfilt(b, a, timeseries, axis=0)

        ALFF = np.std(ts_filt, axis=0)
        PSD_tot = np.std(timeseries, axis=0)

        fALFF = np.divide(ALFF, PSD_tot)
        alff_img = nimg.new_img_like(data, ALFF)
        falff_img = nimg.new_img_like(data, fALFF)
        return alff_img, falff_img

    @lru_cache(maxsize=None, typed=True)  # noqa: B019
    def _compute(
        self,
        data: Union["Nifti1Image", "Nifti2Image"],
        highpass: float,
        lowpass: float,
        order: int,
        tr: Optional[float],
    ) -> Tuple["Nifti1Image", "Nifti1Image"]:
        """Compute the ALFF map with memorization.

        Parameters
        ----------
        data : 4D Niimg-like object
            Images to process.
        highpass : float
            Highpass cutoff frequency.
        lowpass : float
            Lowpass cutoff frequency.
        order : int
            Order of the filter.
        tr : float, optional
            The Repetition Time of the BOLD data.

        Returns
        -------
        alff: Niimg-like object
            ALFF map.
        falff: Niimg-like object
            fALFF map.
        """
        if self.use_afni:
            output = self._compute_alff_afni(
                data=data,
                highpass=highpass,
                lowpass=lowpass,
                tr=tr,
            )
        else:
            output = self._compute_alff_python(
                data, highpass=highpass, lowpass=lowpass, order=order, tr=tr
            )
        return output

    def fit_transform(
        self,
        input_data: Dict[str, Any],
        highpass: float,
        lowpass: float,
        order: int,
        tr: Optional[float],
    ) -> Tuple["Nifti1Image", "Nifti1Image"]:
        """Fit and transform for the estimator.

        Parameters
        ----------
        input_data : dict
            The BOLD data as dictionary.
        highpass : float
            Highpass cutoff frequency.
        lowpass : float
            Lowpass cutoff frequency.
        order : int
            Order of the filter.
        tr : float, optional
            The Repetition Time of the BOLD data.

        Returns
        -------
        alff: Niimg-like object
            ALFF map.
        falff: Niimg-like object
            fALFF map.
        """
        bold_path = input_data["path"]
        bold_data = input_data["data"]
        # Clear cache if file path is different from when caching was done
        if self._file_path != bold_path:
            logger.info(f"Removing fALFF map cache at {self._file_path}.")
            # Clear the cache
            self._compute.cache_clear()
            # Clear temporary directory files
            for file_ in self.temp_dir_path.iterdir():
                file_.unlink(missing_ok=True)
            # Set the new file path
            self._file_path = bold_path
        else:
            logger.info(f"Using fALFF map cache at {self._file_path}.")
        # Compute
        return self._compute(
            data=bold_data,
            highpass=highpass,
            lowpass=lowpass,
            order=order,
            tr=tr,
        )
