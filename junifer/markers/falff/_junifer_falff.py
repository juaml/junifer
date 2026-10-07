"""Provide class for computing ALFF using junifer."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from functools import lru_cache
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    ClassVar,
)

import nibabel as nib
import numpy as np
import scipy as sp
from nilearn import image as nimg

from ...pipeline import WorkDirManager
from ...typing import Dependencies
from ...utils.singleton import Singleton
from ..base import logger


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
        tr: float | None,
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

        # Get scan data (no extra copy, don't keep nibabel's cached copy)
        niimg = nib.load(input_path)
        niimg_data = niimg.get_fdata(caching="unchanged")
        if tr is None:
            tr = float(niimg.header["pixdim"][4])  # type: ignore
            logger.info(f"`tr` not provided, using `tr` from header: {tr}")

        n_timepoints = niimg_data.shape[-1]
        # One-sided spectrum of a real signal; weights reproduce the
        # two-sided sums (each non-zero bin appears twice, Nyquist once)
        fft_freqs = sp.fft.rfftfreq(n_timepoints, tr)
        weights = np.full(fft_freqs.shape, 2.0)
        weights[0] = 0.0  # exclude DC
        if n_timepoints % 2 == 0:
            weights[-1] = 1.0  # Nyquist bin appears only once
        band_weights = np.where(
            (fft_freqs > highpass) & (fft_freqs < lowpass), weights, 0.0
        )
        logger.info(
            f"FFT: nfft = {n_timepoints}, "
            f"dFreq = {fft_freqs[1] - fft_freqs[0]}, "
            f"nyquist = {fft_freqs[-1]}"
        )

        # Process voxels in chunks to bound FFT memory
        flat = niimg_data.reshape(-1, n_timepoints)
        numerator = np.empty(flat.shape[0])
        denominator = np.empty(flat.shape[0])
        chunk = 20_000
        for start in range(0, flat.shape[0], chunk):
            amp = np.abs(sp.fft.rfft(flat[start : start + chunk], axis=-1))
            denominator[start : start + chunk] = amp @ weights
            numerator[start : start + chunk] = amp @ band_weights
        spatial_shape = niimg_data.shape[:-1]
        numerator = numerator.reshape(spatial_shape)
        denominator = denominator.reshape(spatial_shape)
        del niimg_data, flat

        # Compute fALFF, but avoid division by zero
        denom_mask = denominator <= 0.000001
        denominator[denom_mask] = 1
        falff = np.divide(numerator, denominator)
        falff[denom_mask] = 0

        # Calculate ALFF
        alff = numerator / np.sqrt(n_timepoints)
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
