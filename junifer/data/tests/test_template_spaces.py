"""Provide tests for template spaces."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import socket
from pathlib import Path

import nibabel as nib
import pytest

from junifer.data import get_template, get_xfm
from junifer.datareader import DefaultDataReader
from junifer.testing.datagrabbers import (
    OasisVBMTestingDataGrabber,
    PartlyCloudyTestingDataGrabber,
)


@pytest.mark.skipif(
    socket.gethostname() != "juseless",
    reason="only for juseless",
)
def test_get_xfm(tmp_path: Path) -> None:
    """Test warp file fetching.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    xfm_path = get_xfm(
        src="MNI152NLin6Asym", dst="MNI152NLin2009cAsym", xfms_dir=tmp_path
    )
    assert isinstance(xfm_path, Path)


@pytest.mark.parametrize(
    "template_type",
    [
        "T1w",
        "brain",
        "gm",
        "wm",
        "csf",
    ],
)
def test_get_template(template_type: str) -> None:
    """Test tailored template image fetch.

    Parameters
    ----------
    template_type : str
        The parametrized template type.

    """
    with PartlyCloudyTestingDataGrabber() as dg:
        element = dg["sub-01"]
        element_data = DefaultDataReader().fit_transform(element)
        bold = element_data["BOLD"]
        # Get tailored parcellation
        tailored_template = get_template(
            space=bold["space"],
            target_img=bold["data"],
            template_type=template_type,
        )
        assert isinstance(tailored_template, nib.Nifti1Image)


def test_get_template_invalid_space() -> None:
    """Test invalid space check for template fetch."""
    with OasisVBMTestingDataGrabber() as dg:
        element = dg["sub-01"]
        element_data = DefaultDataReader().fit_transform(element)
        vbm_gm = element_data["VBM_GM"]
        # Get tailored parcellation
        with pytest.raises(ValueError, match="Unknown template space:"):
            get_template(space="andromeda", target_img=vbm_gm["data"])


def test_get_template_invalid_template_type() -> None:
    """Test invalid template type check for template fetch."""
    with OasisVBMTestingDataGrabber() as dg:
        element = dg["sub-01"]
        element_data = DefaultDataReader().fit_transform(element)
        vbm_gm = element_data["VBM_GM"]
        # Get tailored parcellation
        with pytest.raises(ValueError, match="Unknown template type:"):
            get_template(
                space=vbm_gm["space"],
                target_img=vbm_gm["data"],
                template_type="xenon",
            )


def test_get_template_closest_resolution() -> None:
    """Test closest resolution check for template fetch."""
    with OasisVBMTestingDataGrabber() as dg:
        element = dg["sub-01"]
        element_data = DefaultDataReader().fit_transform(element)
        vbm_gm = element_data["VBM_GM"]
        # Change header resolution to fetch closest resolution
        element_data["VBM_GM"]["data"].header.set_zooms((3, 3, 3))
        template = get_template(
            space=vbm_gm["space"], target_img=vbm_gm["data"]
        )
        assert isinstance(template, nib.Nifti1Image)
