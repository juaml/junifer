"""Provide tests for Smoothing."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

import nibabel as nib
import pytest

from junifer.datareader import DefaultDataReader
from junifer.pipeline.utils import _check_afni, _check_fsl
from junifer.preprocess import Smoothing, SmoothingImpl
from junifer.testing.datagrabbers import SPMAuditoryTestingDataGrabber


pytestmark = pytest.mark.external


@pytest.mark.parametrize(
    "data_type",
    ["T1w", "BOLD"],
)
def test_Smoothing_nilearn(data_type: str) -> None:
    """Test Smoothing using nilearn.

    Parameters
    ----------
    data_type : str
        The parametrized data type.

    """
    with SPMAuditoryTestingDataGrabber(n_timepoints=10) as dg:
        # Read data
        element_data = DefaultDataReader().fit_transform(dg["sub001"])
        # Preprocess data
        output = Smoothing(
            using=SmoothingImpl.nilearn,
            on=data_type,
            smoothing_params={"fwhm": "fast"},
        ).fit_transform(element_data)

        assert isinstance(output, dict)
        # The data is loaded from the saved file, not kept in memory
        assert nib.is_proxy(output[data_type]["data"].dataobj)
        assert output[data_type]["data"].get_filename() == str(
            output[data_type]["path"]
        )


@pytest.mark.parametrize(
    "data_type",
    ["T1w", "BOLD"],
)
@pytest.mark.skipif(
    _check_afni() is False, reason="requires AFNI to be in PATH"
)
def test_Smoothing_afni(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, data_type: str
) -> None:
    """Test Smoothing using AFNI.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    monkeypatch : pytest.MonkeyPatch
        The pytest.MonkeyPatch object.
    data_type : str
        The parametrized data type.

    """
    # Run in an empty directory, to check that no files are written in it
    monkeypatch.chdir(tmp_path)
    with SPMAuditoryTestingDataGrabber(n_timepoints=10) as dg:
        # Read data
        element_data = DefaultDataReader().fit_transform(dg["sub001"])
        # Preprocess data
        output = Smoothing(
            using=SmoothingImpl.afni,
            on=data_type,
            smoothing_params={"fwhm": 3},
        ).fit_transform(element_data)

        assert isinstance(output, dict)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "data_type",
    ["T1w", "BOLD"],
)
@pytest.mark.skipif(_check_fsl() is False, reason="requires FSL to be in PATH")
def test_Smoothing_fsl(data_type: str) -> None:
    """Test Smoothing using FSL.

    Parameters
    ----------
    data_type : str
        The parametrized data type.

    """
    with SPMAuditoryTestingDataGrabber(n_timepoints=10) as dg:
        # Read data
        element_data = DefaultDataReader().fit_transform(dg["sub001"])
        # Preprocess data
        output = Smoothing(
            using=SmoothingImpl.fsl,
            on=data_type,
            smoothing_params={"brightness_threshold": 10.0, "fwhm": 3.0},
        ).fit_transform(element_data)

        assert isinstance(output, dict)
