"""Provide tests for the warping utilities."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from pathlib import Path

import nibabel as nib
import numpy as np
import pytest
from numpy.testing import assert_array_equal

from junifer.datagrabber import DataType
from junifer.datareader import DefaultDataReader
from junifer.pipeline.utils import _check_ants
from junifer.preprocess import SpaceWarper, SpaceWarpingImpl
from junifer.preprocess.warping._utils import warp_in_chunks
from junifer.testing import config_override
from junifer.testing.datagrabbers import PartlyCloudyTestingDataGrabber


def _copy(in_path: Path, out_path: Path) -> list[str]:
    """Return a command copying the image, to test the chunks."""
    return ["cp", str(in_path), str(out_path)]


@pytest.mark.parametrize("suffix", [".nii", ".nii.gz"])
@pytest.mark.parametrize(
    "n_volumes, chunk_size", [(10, 3), (10, 5), (10, 10), (10, 100), (1, 1)]
)
@pytest.mark.parametrize("dtype", [np.float32, np.float64, np.int16])
def test_warp_in_chunks(
    tmp_path: Path,
    suffix: str,
    n_volumes: int,
    chunk_size: int,
    dtype: type,
) -> None:
    """Test warping in chunks gives the same image.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    suffix : str
        The parametrized file extension.
    n_volumes : int
        The parametrized number of volumes.
    chunk_size : int
        The parametrized number of volumes of the chunks.
    dtype : type
        The parametrized data type of the image.

    """
    rng = np.random.default_rng(0)
    data = rng.normal(size=(4, 5, 6, n_volumes)) * 100
    img = nib.Nifti1Image(data.astype(dtype), np.diag([2, 2, 2, 1]))
    if dtype is np.int16:
        # Scaled data
        img.header.set_slope_inter(0.5, 10)
    in_path = tmp_path / f"input{suffix}"
    out_path = tmp_path / f"output{suffix}"
    nib.save(img, in_path)
    with config_override("preprocessing.warping.chunksize", chunk_size):
        warp_in_chunks(
            name="cp",
            input_path=in_path,
            output_path=out_path,
            cmd=_copy,
            tempdir=tmp_path,
        )
    out = nib.load(out_path)
    expected = nib.load(in_path)
    assert out.shape == expected.shape
    if dtype is not np.int16:
        assert out.get_data_dtype() == expected.get_data_dtype()
    assert_array_equal(out.affine, expected.affine)
    assert_array_equal(out.get_fdata(), expected.get_fdata())
    # Only the input and the output are left
    assert sorted(p.name for p in tmp_path.iterdir()) == sorted(
        [in_path.name, out_path.name]
    )


def test_warp_in_chunks_3d(tmp_path: Path) -> None:
    """Test warping a 3D image is not done in chunks.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    img = nib.Nifti1Image(np.ones((4, 5, 6), dtype=np.float32), np.eye(4))
    in_path = tmp_path / "input.nii.gz"
    out_path = tmp_path / "output.nii.gz"
    nib.save(img, in_path)
    calls = []

    def cmd(in_path: Path, out_path: Path) -> list[str]:
        calls.append(in_path)
        return _copy(in_path, out_path)

    with config_override("preprocessing.warping.chunksize", 1):
        warp_in_chunks(
            name="cp",
            input_path=in_path,
            output_path=out_path,
            cmd=cmd,
            tempdir=tmp_path,
        )
    assert calls == [in_path]
    assert_array_equal(nib.load(out_path).get_fdata(), img.get_fdata())


@pytest.mark.parametrize("chunk_size", [0, -1, 2.5, "10"])
def test_warp_in_chunks_error(tmp_path: Path, chunk_size: object) -> None:
    """Test an invalid chunk size.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    chunk_size : object
        The parametrized invalid chunk size.

    """
    with config_override("preprocessing.warping.chunksize", chunk_size):
        with pytest.raises(ValueError, match="must be a positive integer"):
            warp_in_chunks(
                name="cp",
                input_path=tmp_path / "input.nii.gz",
                output_path=tmp_path / "output.nii.gz",
                cmd=_copy,
                tempdir=tmp_path,
            )


@pytest.mark.external
@pytest.mark.skipif(
    _check_ants() is False, reason="requires ANTs to be in PATH"
)
def test_SpaceWarper_ants_chunks() -> None:
    """Test warping with ANTs in chunks gives the same data."""
    outputs = []
    for chunk_size in (100, 3):
        with PartlyCloudyTestingDataGrabber(n_timepoints=8) as dg:
            element_data = DefaultDataReader().fit_transform(dg["sub-01"])
            with config_override(
                "preprocessing.warping.chunksize", chunk_size
            ):
                output = SpaceWarper(
                    using=SpaceWarpingImpl.ants,
                    reference="MNI152NLin6Asym",
                    on=DataType.BOLD,
                ).preprocess(
                    input=element_data["BOLD"],
                    extra_input=element_data,
                )
            assert output["data"].get_data_dtype() == np.float32
            outputs.append(np.asarray(output["data"].dataobj))
    assert outputs[0].shape[-1] == 8
    assert_array_equal(outputs[0], outputs[1])
