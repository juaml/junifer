"""Provide estimator class for (f)ALFF."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
#          Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

import shutil
import subprocess
import tempfile
import typing
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple, Union

import nibabel as nib
import numpy as np
from nilearn import image as nimg
from scipy.fft import fft, fftfreq

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

    def __init__(self) -> None:
        self._file_path = None
        # Create temporary directory for intermittent storage of assets during
        # computation via afni's 3dReHo
        self.temp_dir_path = Path(tempfile.mkdtemp())

    def __del__(self) -> None:
        """Cleanup."""
        print("Cleaning up temporary directory...")
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
        # TODO: Figure out how to capture stdout and stderr
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
        highpass : positive float
            Highpass cutoff frequency.
        lowpass : positive float
            Lowpass cutoff frequency.
        tr : positive float, optional
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

        params_suffix = f"_{highpass}_{lowpass}_{tr}"
        alff_fname = self.temp_dir_path / f"alff{params_suffix}.nii"
        falff_fname = self.temp_dir_path / f"falff{params_suffix}.nii"

        # Use afni's 3dRSFC to compute ALFF and fALFF
        falff_afni_out_path_prefix = self.temp_dir_path / "temp_falff"

        bp_cmd = (
            "3dRSFC "
            f"-prefix {falff_afni_out_path_prefix.resolve()} "
            f"-input {nifti_in_file_path.resolve()} "
            f"-band {highpass} {lowpass} "
            "-no_rsfa -nosat -nodetrend "
        )
        if tr is not None:
            bp_cmd += f"-dt {tr} "
        self._run_afni_cmd(bp_cmd)

        # Convert afni's output to nifti
        convert_cmd = (
            "3dAFNItoNIFTI "
            f"-prefix {alff_fname.resolve()} "
            f"{falff_afni_out_path_prefix}_ALFF+tlrc.BRIK "
        )
        self._run_afni_cmd(convert_cmd)

        convert_cmd = (
            "3dAFNItoNIFTI "
            f"-prefix {falff_fname.resolve()} "
            f"{falff_afni_out_path_prefix}_fALFF+tlrc.BRIK "
        )
        self._run_afni_cmd(convert_cmd)

        # Cleanup intermediate files
        for fname in self.temp_dir_path.glob("temp_*"):
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
        tr: Optional[float],
    ) -> Tuple["Nifti1Image", "Nifti1Image"]:
        """Compute (f)ALFF map.

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
        alff: Niimg-like object
            ALFF map.
        falff: Niimg-like object
            fALFF map.
        """
        timeseries = data.get_fdata().copy()
        if tr is None:
            tr = float(data.header["pixdim"][4])  # type: ignore
            logger.info(f"TR Not provided, using TR from header = {tr}")
        # bandpass the data within the lowpass and highpass cutoff freqs

        ts_fft = fft(timeseries, axis=-1)
        ts_fft = typing.cast(np.ndarray, ts_fft)
        fft_freqs = np.abs(fftfreq(timeseries.shape[-1], tr))

        dFreq = fft_freqs[1] - fft_freqs[0]
        nyquist = np.max(fft_freqs)
        nfft = len(fft_freqs)
        logger.info(
            f"FFT: nfft = {nfft}, dFreq = {dFreq}, nyquist = {nyquist}"
        )

        # First compute the denominator on the broadband signal
        all_freq_mask = fft_freqs > 0
        denominator = np.sum(np.abs(ts_fft[..., all_freq_mask]), axis=-1)

        # Compute the numerator on the bandpassed signal
        freq_mask = np.logical_and(fft_freqs > highpass, fft_freqs < lowpass)
        # Compute ALFF
        numerator = np.sum(np.abs(ts_fft[..., freq_mask]), axis=-1)

        # Compute fALFF, but avoid division by zero
        denom_mask = denominator <= 0.000001
        denominator[denom_mask] = 1  # set to 1 to avoid division by zero
        python_falff = np.divide(numerator, denominator)
        # Set the values where denominator is zero to zero
        python_falff[denom_mask] = 0

        python_alff = numerator / np.sqrt(timeseries.shape[-1])
        alff_img = nimg.new_img_like(data, python_alff)
        falff_img = nimg.new_img_like(data, python_falff)
        return alff_img, falff_img

    @lru_cache(maxsize=None, typed=True)  # noqa: B019
    def _compute(
        self,
        use_afni: bool,
        data: Union["Nifti1Image", "Nifti2Image"],
        highpass: float,
        lowpass: float,
        tr: Optional[float],
    ) -> Tuple["Nifti1Image", "Nifti1Image"]:
        """Compute the ALFF map with memorization.

        Parameters
        ----------
        use_afni : bool
            Whether to use AFNI for computing.
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
        alff: Niimg-like object
            ALFF map.
        falff: Niimg-like object
            fALFF map.
        """
        if use_afni:
            output = self._compute_alff_afni(
                data=data,
                highpass=highpass,
                lowpass=lowpass,
                tr=tr,
            )
        else:
            output = self._compute_alff_python(
                data, highpass=highpass, lowpass=lowpass, tr=tr
            )
        return output

    def fit_transform(
        self,
        use_afni: bool,
        input_data: Dict[str, Any],
        highpass: float,
        lowpass: float,
        tr: Optional[float],
    ) -> Tuple["Nifti1Image", "Nifti1Image"]:
        """Fit and transform for the estimator.

        Parameters
        ----------
        use_afni : bool
            Whether to use AFNI for computing.
        input_data : dict
            The BOLD data as dictionary.
        highpass : positive float
            Highpass cutoff frequency.
        lowpass : positive float
            Lowpass cutoff frequency.
        tr : positive float, optional
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
            use_afni=use_afni,
            data=bold_data,
            highpass=highpass,
            lowpass=lowpass,
            tr=tr,
        )
