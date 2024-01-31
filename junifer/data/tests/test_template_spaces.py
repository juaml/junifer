"""Provide tests for template spaces."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import socket
from pathlib import Path

import pytest

from junifer.data import get_xfm


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
