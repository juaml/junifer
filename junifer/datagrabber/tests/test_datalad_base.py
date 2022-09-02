"""Provide tests for datalad_base."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import pytest

from junifer.datagrabber.datalad_base import DataladDataGrabber


def test_datalad_base_abstractness() -> None:
    """Test datalad base is abstract."""
    with pytest.raises(TypeError, match=r"abstract"):
        DataladDataGrabber()


# def test_datalad_base_missing_uri() -> None:
#     """Test proper check of missing URI in datalad base initialization."""
#     with pytest.raises(ValueError, match=r"`uri` must be provided"):
#         DataladDataGrabber(

#         )
