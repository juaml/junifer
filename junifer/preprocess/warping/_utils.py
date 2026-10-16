"""Provide utilities for warping."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from collections.abc import Callable
from pathlib import Path

import nibabel as nib
import numpy as np
from tqdm import tqdm

from ...utils import config, raise_error, run_ext_cmd
from ..base import logger


__all__ = ["warp_in_chunks"]


def warp_in_chunks(
    name: str,
    input_path: Path,
    output_path: Path,
    cmd: Callable[[Path, Path], list[str]],
    tempdir: Path,
) -> None:
    """Warp an image, in chunks of volumes if it is 4D.

    The memory used by the warping commands grows with the number of volumes,
    so the volumes of a 4D image are warped in chunks of
    ``preprocessing.warping.chunksize`` volumes (default 100), which are then
    concatenated. The volumes are warped independently, so the result is the
    same as warping the whole image.

    Parameters
    ----------
    name : str
        The name of the warping command.
    input_path : pathlib.Path
        The path of the image to warp.
    output_path : pathlib.Path
        The path of the warped image.
    cmd : callable
        A function that returns the command to warp an image, given the paths
        of the image to warp and of the warped image.
    tempdir : pathlib.Path
        The directory for the chunks.

    Raises
    ------
    ValueError
        If ``preprocessing.warping.chunksize`` is not a positive integer.

    """
    chunk_size = config.get("preprocessing.warping.chunksize", 100)
    if (
        isinstance(chunk_size, bool)
        or not isinstance(chunk_size, int)
        or chunk_size < 1
    ):
        raise_error(
            "`preprocessing.warping.chunksize` must be a positive integer, "
            f"but is {chunk_size}"
        )
    img = nib.load(input_path)
    if img.ndim != 4 or img.shape[3] <= chunk_size:
        run_ext_cmd(name=name, cmd=cmd(input_path, output_path))
        return

    n_volumes = img.shape[3]
    starts = range(0, n_volumes, chunk_size)
    logger.info(
        f"Warping {n_volumes} volumes in {len(starts)} chunks of up to "
        f"{chunk_size} volumes"
    )
    warped_chunks = []
    for i, start in enumerate(tqdm(starts, desc=f"{name} chunks")):
        # Uncompressed, as they are deleted right after being read
        chunk_path = tempdir / f"chunk{i}_input_{output_path.stem}.nii"
        warped_chunk_path = tempdir / f"chunk{i}_{output_path.stem}.nii"
        chunk = img.slicer[..., start : start + chunk_size]
        # The data is read scaled, so save it as float instead of scaling it
        # again (with a different scaling) in its data type
        if img.dataobj.slope != 1 or img.dataobj.inter != 0:
            chunk.set_data_dtype(np.float32)
        nib.save(chunk, chunk_path)
        run_ext_cmd(name=name, cmd=cmd(chunk_path, warped_chunk_path))
        chunk_path.unlink()
        warped_chunks.append(warped_chunk_path)

    # Fill the data of the warped image with the warped chunks (instead of
    # concatenating them, which needs twice the memory)
    data = None
    for start, warped_chunk_path in zip(starts, warped_chunks, strict=True):
        warped_chunk = nib.load(warped_chunk_path)
        chunk_data = np.asanyarray(warped_chunk.dataobj)
        if data is None:
            first = warped_chunk
            data = np.empty(
                (*chunk_data.shape[:3], n_volumes), dtype=chunk_data.dtype
            )
        data[..., start : start + chunk_data.shape[3]] = chunk_data
        warped_chunk_path.unlink()
    warped = nib.Nifti1Image(data, first.affine, first.header)
    warped.set_data_dtype(data.dtype)
    nib.save(warped, output_path)
