"""Provide class for computing ALFF using junifer."""

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
import numpy as np
import scipy as sp
from nilearn import image as nimg

from ...pipeline import WorkDirManager
from ...typing import Dependencies
from ...utils import logger
from ...utils.singleton import Singleton


if TYPE_CHECKING:
    from nibabel.nifti1 import Nifti1Image


__all__ = ["JuniferALFF"]


class JuniferALFF(metaclass=Singleton):
    """Class for computing ALFF using junifer.

    It's designed as a singleton with caching for efficient computation.

    """

    _DEPENDENCIES: ClassVar[Dependencies] = {"numpy", "nilearn", "scipy"}

    def __del__(self) -> None:
        """Terminate the class."""
        # Clear the computation cache
        logger.debug("Clearing cache for ALFF computation via junifer")
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
        logger.debug("Creating cache for ALFF computation via junifer")

        # Get scan data
        niimg = nib.load(input_path)
        niimg_data = niimg.get_fdata().copy()
        if tr is None:
            tr = float(niimg.header["pixdim"][4])  # type: ignore
            logger.info(f"`tr` not provided, using `tr` from header: {tr}")

        # Bandpass the data within the lowpass and highpass cutoff freqs
        fft_data = sp.fft.fft(niimg_data, axis=-1)
        fft_freqs = np.abs(sp.fft.fftfreq(niimg_data.shape[-1], tr))
        # Frequency difference
        fft_freqs_diff = fft_freqs[1] - fft_freqs[0]
        # Nyquist frequency
        nyquist = np.max(fft_freqs)
        # FFT sample frequency count
        n_fft = len(fft_freqs)
        logger.info(
            f"FFT: nfft = {n_fft}, dFreq = {fft_freqs_diff}, "
            f"nyquist = {nyquist}"
        )

        # Compute the denominator on the broadband signal
        all_freq_mask = fft_freqs > 0
        denominator = np.sum(np.abs(fft_data[..., all_freq_mask]), axis=-1)

        # Compute the numerator on the bandpassed signal
        freq_mask = np.logical_and(fft_freqs > highpass, fft_freqs < lowpass)

        # Compute ALFF
        numerator = np.sum(np.abs(fft_data[..., freq_mask]), axis=-1)

        # Compute fALFF, but avoid division by zero
        denom_mask = denominator <= 0.000001
        denominator[denom_mask] = 1  # set to 1 to avoid division by zero
        # Calculate fALFF
        falff = np.divide(numerator, denominator)
        # Set the values where denominator is zero to zero
        falff[denom_mask] = 0

        # Calculate ALFF
        alff = numerator / np.sqrt(niimg_data.shape[-1])
        alff_data = nimg.new_img_like(
            ref_niimg=niimg,
            data=alff,
        )
        falff_data = nimg.new_img_like(
            ref_niimg=niimg,
            data=falff,
        )

        # Create element-scoped tempdir
        element_tempdir = WorkDirManager().get_element_tempdir(
            prefix="junifer_lff"
        )
        output_alff_path = element_tempdir / "output_alff.nii.gz"
        output_falff_path = element_tempdir / "output_falff.nii.gz"
        # Save computed data to file
        nib.save(alff_data, output_alff_path)
        nib.save(falff_data, output_falff_path)

        return alff_data, falff_data, output_alff_path, output_falff_path  # type: ignore
