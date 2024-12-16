"""Provide tests for coordinates."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import numpy as np
import pytest
from numpy.testing import assert_array_equal

from junifer.data import CoordinatesRegistry
from junifer.datareader import DefaultDataReader
from junifer.testing.datagrabbers import OasisVBMTestingDataGrabber


def test_register_built_in_check() -> None:
    """Test coordinates registration check for built-in coordinates."""
    with pytest.raises(ValueError, match=r"built-in"):
        CoordinatesRegistry().register(
            name="DMNBuckner",
            coordinates=np.zeros(2),
            voi_names=["1", "2"],
            space="MNI",
        )


def test_register_overwrite() -> None:
    """Test coordinates registration check for overwriting."""
    CoordinatesRegistry().register(
        name="MyList",
        coordinates=np.zeros((2, 3)),
        voi_names=["roi1", "roi2"],
        space="MNI",
    )
    with pytest.raises(ValueError, match=r"already registered"):
        CoordinatesRegistry().register(
            name="MyList",
            coordinates=np.ones((2, 3)),
            voi_names=["roi2", "roi3"],
            space="MNI",
            overwrite=False,
        )

    CoordinatesRegistry().register(
        name="MyList",
        coordinates=np.ones((2, 3)),
        voi_names=["roi2", "roi3"],
        space="MNI",
        overwrite=True,
    )

    coord, names, space = CoordinatesRegistry().load("MyList")
    assert_array_equal(coord, np.ones((2, 3)))
    assert names == ["roi2", "roi3"]
    assert space == "MNI"


def test_register_valid_input() -> None:
    """Test coordinates registration check for valid input."""
    with pytest.raises(TypeError, match=r"numpy.ndarray"):
        CoordinatesRegistry().register(
            name="MyList",
            coordinates=[1, 2],
            voi_names=["roi1", "roi2"],
            space="MNI",
            overwrite=True,
        )
    with pytest.raises(ValueError, match=r"2D array"):
        CoordinatesRegistry().register(
            name="MyList",
            coordinates=np.zeros((2, 3, 4)),
            voi_names=["roi1", "roi2"],
            space="MNI",
            overwrite=True,
        )

    with pytest.raises(ValueError, match=r"3 values"):
        CoordinatesRegistry().register(
            name="MyList",
            coordinates=np.zeros((2, 4)),
            voi_names=["roi1", "roi2"],
            space="MNI",
            overwrite=True,
        )
    with pytest.raises(ValueError, match=r"voi_names"):
        CoordinatesRegistry().register(
            name="MyList",
            coordinates=np.zeros((2, 3)),
            voi_names=["roi1", "roi2", "roi3"],
            space="MNI",
            overwrite=True,
        )


def test_list() -> None:
    """Test listing of available coordinates."""
    assert {"DMNBuckner", "MultiTask", "VigAtt", "WM"}.issubset(
        set(CoordinatesRegistry().list)
    )


def test_load() -> None:
    """Test loading coordinates from file."""
    coord, names, space = CoordinatesRegistry().load("DMNBuckner")
    assert coord.shape == (6, 3)  # type: ignore
    assert names == ["PCC", "MPFC", "lAG", "rAG", "lHF", "rHF"]
    assert space == "MNI"


def test_load_nonexisting() -> None:
    """Test loading coordinates that not exist."""
    with pytest.raises(ValueError, match=r"not found"):
        CoordinatesRegistry().load("NonExisting")


def test_get() -> None:
    """Test tailored coordinates fetch."""
    reader = DefaultDataReader()
    with OasisVBMTestingDataGrabber() as dg:
        element = dg["sub-01"]
        element_data = reader.fit_transform(element)
        vbm_gm = element_data["VBM_GM"]
        # Get tailored coordinates
        tailored_coords, tailored_labels = CoordinatesRegistry().get(
            coords="DMNBuckner", target_data=vbm_gm
        )
        # Get raw coordinates
        raw_coords, raw_labels, _ = CoordinatesRegistry().load("DMNBuckner")
        # Both tailored and raw should be same for now
        assert_array_equal(tailored_coords, raw_coords)
        assert tailored_labels == raw_labels
