"""Provide class for computing ALFF using junifer."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from functools import lru_cache
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    ClassVar,
    Optional,
    Set,
    Tuple,
)

import nibabel as nib
import numpy as np
import scipy as sp
from nilearn import image as nimg

from ...pipeline import WorkDirManager
from ...pipeline.singleton import singleton
from ...utils import logger


if TYPE_CHECKING:
    from nibabel import Nifti1Image


__all__ = ["JuniferALFF"]


@singleton
class JuniferALFF:
    """Class for computing ALFF using junifer.

    It's designed as a singleton with caching for efficient computation.

    """

    _DEPENDENCIES: ClassVar[Set[str]] = {"numpy", "nilearn", "scipy"}

    def __del__(self) -> None:
        """Terminate the class."""
        # Clear the computation cache
        logger.debug("Clearing cache for ALFF computation via junifer")
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
        logger.debug("Creating cache for ALFF computation via junifer")

        # Get scan data
        niimg_data = data.get_fdata().copy()
        if tr is None:
            tr = float(data.header["pixdim"][4])  # type: ignore
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
            ref_niimg=data,
            data=alff,
        )
        falff_data = nimg.new_img_like(
            ref_niimg=data,
            data=falff,
        )

        # Create element-scoped tempdir so that the ALFF and fALFF maps are
        # available later as nibabel stores file path reference for
        # loading on computation
        element_tempdir = WorkDirManager().get_element_tempdir(
            prefix="junifer_alff+falff"
        )
        output_alff_path = element_tempdir / "output_alff.nii.gz"
        output_falff_path = element_tempdir / "output_falff.nii.gz"
        # Save computed data to file
        nib.save(alff_data, output_alff_path)
        nib.save(falff_data, output_falff_path)

        return alff_data, falff_data, output_alff_path, output_falff_path  # type: ignore
