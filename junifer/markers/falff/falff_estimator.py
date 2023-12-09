"""Provide estimator class for (f)ALFF."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
#          Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

import subprocess
import typing
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple, Union, cast

import nibabel as nib
import numpy as np
from nilearn import image as nimg
from scipy.fft import fft, fftfreq

from ...pipeline import WorkDirManager
from ...pipeline.singleton import singleton
from ...utils import logger, raise_error


if TYPE_CHECKING:
    from nibabel import Nifti1Image, Nifti2Image


@singleton
class ALFFEstimator:
    """Estimator class for (fractional) Amplitude Low Frequency Fluctuation.

    This class is a singleton and is used for efficient computation of fALFF,
    by caching the voxel-wise ALFF map for a given set of file path and
    computation parameters.

    .. warning:: This class can only be used via :class:`.ALFFBase` as it
    serves a specific purpose.

    Attributes
    ----------
    temp_dir_path : pathlib.Path
        Path to the temporary directory for assets storage.

    """

    def __init__(self) -> None:
        self._file_path = None
        # Create temporary directory for intermittent storage of assets during
        # computation via afni's 3dRSFC
        self.temp_dir_path = None

    def __del__(self) -> None:
        """Cleanup."""
        # Delete temporary directory and ignore errors for read-only files
        if self.temp_dir_path is not None:
            WorkDirManager().delete_tempdir(self.temp_dir_path)

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
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
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
    ) -> Tuple["Nifti1Image", "Nifti1Image", Path, Path]:
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
        Niimg-like object
            ALFF map.
        Niimg-like object
            fALFF map.
        pathlib.Path
            The path to the ALFF map as NIfTI.
        pathlib.Path
            The path to the fALFF map as NIfTI.

        Raises
        ------
        RuntimeError
            If the AFNI commands fails due to some issues.

        """
        # Note: self.temp_dir_path is sure to exist before proceeding, so
        #       types checks are ignored further on.

        # Save niimg to nii.gz
        nifti_in_file_path = self.temp_dir_path / "input.nii"  # type: ignore
        nib.save(data, nifti_in_file_path)

        params_suffix = f"_{highpass}_{lowpass}_{tr}"
        # Create element-scoped tempdir so that the ALFF and fALFF maps are
        # available later as get_coordinates and the like need it
        # in fALFFSpheres and the like to transform to other template
        # spaces
        element_tempdir = WorkDirManager().get_element_tempdir(
            prefix="alff_falff_afni"
        )
        alff_fname = element_tempdir / f"alff{params_suffix}.nii"
        falff_fname = element_tempdir / f"falff{params_suffix}.nii"

        # Use afni's 3dRSFC to compute ALFF and fALFF
        falff_afni_out_path_prefix = (
            self.temp_dir_path / "temp_falff"  # type: ignore
        )

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
        for fname in self.temp_dir_path.glob("temp_*"):  # type: ignore
            fname.unlink()

        # Load niftis
        alff_img = nib.load(alff_fname)
        falff_img = nib.load(falff_fname)
        # Cast image type
        alff_img = cast("Nifti1Image", alff_img)
        falff_img = cast("Nifti1Image", falff_img)
        return alff_img, falff_img, alff_fname, falff_fname

    def _compute_alff_python(
        self,
        data: Union["Nifti1Image", "Nifti2Image"],
        highpass: float,
        lowpass: float,
        tr: Optional[float],
    ) -> Tuple["Nifti1Image", "Nifti1Image", Path, Path]:
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
        Niimg-like object
            ALFF map.
        Niimg-like object
            fALFF map.
        pathlib.Path
            The path to the ALFF map as NIfTI.
        pathlib.Path
            The path to the fALFF map as NIfTI.

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
        # Create element-scoped tempdir so that the ALFF and fALFF maps are
        # available later as get_coordinates and the like need it
        # in fALFFSpheres and the like to transform to other template
        # spaces
        element_tempdir = WorkDirManager().get_element_tempdir(
            prefix="alff_falff_python"
        )
        alff_output_path = element_tempdir / "alff_map_python.nii.gz"
        falff_output_path = element_tempdir / "falff_map_python.nii.gz"
        nib.save(alff_img, alff_output_path)
        nib.save(falff_img, falff_output_path)
        return alff_img, falff_img, alff_output_path, falff_output_path  # type: ignore

    @lru_cache(maxsize=None, typed=True)
    def _compute(
        self,
        use_afni: bool,
        data: Union["Nifti1Image", "Nifti2Image"],
        highpass: float,
        lowpass: float,
        tr: Optional[float],
    ) -> Tuple["Nifti1Image", "Nifti1Image", Path, Path]:
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
        Niimg-like object
            ALFF map.
        Niimg-like object
            fALFF map.
        pathlib.Path
            The path to the ALFF map as NIfTI.
        pathlib.Path
            The path to the fALFF map as NIfTI.

        """
        if use_afni:
            # Create new temporary directory before using AFNI
            self.temp_dir_path = WorkDirManager().get_tempdir(prefix="falff")
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
    ) -> Tuple["Nifti1Image", "Nifti1Image", Path, Path]:
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
        Niimg-like object
            ALFF map.
        Niimg-like object
            fALFF map.
        pathlib.Path
            The path to the ALFF map as NIfTI.
        pathlib.Path
            The path to the fALFF map as NIfTI.

        """
        bold_path = input_data["path"]
        bold_data = input_data["data"]
        # Clear cache if file path is different from when caching was done
        if self._file_path != bold_path:
            logger.info(f"Removing fALFF map cache at {self._file_path}.")
            # Clear the cache
            self._compute.cache_clear()
            # Clear temporary directory files
            if self.temp_dir_path is not None:
                WorkDirManager().delete_tempdir(self.temp_dir_path)
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
