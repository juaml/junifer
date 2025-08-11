"""Provide tests for maps."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import numpy as np
import pytest
from numpy.testing import assert_array_equal

from junifer.data import (
    deregister_data,
    get_data,
    list_data,
    load_data,
    register_data,
)
from junifer.data.maps._maps import _retrieve_smith
from junifer.datagrabber import PatternDataladDataGrabber
from junifer.datareader import DefaultDataReader


def test_register_built_in_check() -> None:
    """Test maps registration check for built-in maps."""
    with pytest.raises(ValueError, match=r"built-in"):
        register_data(
            kind="maps",
            name="Smith_rsn_10",
            maps_path="testmaps.nii.gz",
            maps_labels=["1", "2"],
            space="MNI",
        )


def test_list_incorrect() -> None:
    """Test incorrect information check for list mapss."""
    assert "testmaps" not in list_data(kind="maps")


def test_register_overwrite() -> None:
    """Test maps registration check for overwriting."""
    register_data(
        kind="maps",
        name="testmaps",
        maps_path="testmaps.nii.gz",
        maps_labels=["1", "2"],
        space="MNI152NLin6Sym",
    )
    with pytest.raises(ValueError, match=r"already registered"):
        register_data(
            kind="maps",
            name="testmaps",
            maps_path="testmaps.nii.gz",
            maps_labels=["1", "2"],
            space="MNI152NLin6Sym",
            overwrite=False,
        )

    register_data(
        kind="maps",
        name="testmaps",
        maps_path="testmaps.nii.gz",
        maps_labels=["1", "2"],
        space="MNI152NLin6Sym",
        overwrite=True,
    )

    assert (
        load_data(
            kind="maps",
            name="testmaps",
            target_space="MNI152NLin6Sym",
            path_only=True,
        )[2].name
        == "testmaps.nii.gz"
    )


def test_register_valid_input() -> None:
    """Test maps registration check for valid input."""
    with pytest.raises(TypeError, match=r"numpy.ndarray"):
        register_data(
            kind="coordinates",
            name="MyList",
            coordinates=[1, 2],
            voi_names=["roi1", "roi2"],
            space="MNI",
            overwrite=True,
        )
    with pytest.raises(ValueError, match=r"2D array"):
        register_data(
            kind="coordinates",
            name="MyList",
            coordinates=np.zeros((2, 3, 4)),
            voi_names=["roi1", "roi2"],
            space="MNI",
            overwrite=True,
        )

    with pytest.raises(ValueError, match=r"3 values"):
        register_data(
            kind="coordinates",
            name="MyList",
            coordinates=np.zeros((2, 4)),
            voi_names=["roi1", "roi2"],
            space="MNI",
            overwrite=True,
        )
    with pytest.raises(ValueError, match=r"voi_names"):
        register_data(
            kind="coordinates",
            name="MyList",
            coordinates=np.zeros((2, 3)),
            voi_names=["roi1", "roi2", "roi3"],
            space="MNI",
            overwrite=True,
        )


def test_list() -> None:
    """Test listing of available coordinates."""
    assert {"Smith_rsn_10", "Smith_bm_70"}.issubset(
        set(list_data(kind="maps"))
    )


def test_load_nonexisting() -> None:
    """Test loading maps that not exist."""
    with pytest.raises(ValueError, match=r"not found"):
        load_data(kind="maps", name="nomaps", target_space="MNI152NLin6Sym")


def test_get() -> None:
    """Test tailored maps fetch."""
    reader = DefaultDataReader()
    with PatternDataladDataGrabber(
        uri="https://github.com/OpenNeuroDatasets/ds005226.git",
        types=["BOLD"],
        patterns={
            "BOLD": {
                "pattern": (
                    "derivatives/pre-processed_data/space-MNI/{subject}/"
                    "{subject-padded}_task-{task}_run-{run}_space-MNI152NLin6Asym"
                    "_res-2_desc-preproc_bold.nii.gz"
                ),
                "space": "MNI152NLin6Asym",
            },
        },
        replacements=["subject", "subject-padded", "task", "run"],
    ) as dg:
        element = dg[("sub-01", "sub-001", "rest", "1")]
        element_data = reader.fit_transform(element)
        bold = element_data["BOLD"]
        # Get tailored coordinates
        tailored_maps, tailored_labels = get_data(
            kind="maps", names="Smith_rsn_10", target_data=bold
        )
        # Get raw maps
        raw_maps, raw_labels, _, _ = load_data(
            kind="maps", name="Smith_rsn_10", target_space="MNI152NLin6Asym"
        )
        # Both tailored and raw should be same for now
        assert_array_equal(tailored_maps.get_fdata(), raw_maps.get_fdata())
        assert tailored_labels == raw_labels


def test_deregister() -> None:
    """Test maps deregistration."""
    deregister_data(kind="maps", name="testmaps")
    assert "testmaps" not in list_data(kind="maps")


@pytest.mark.parametrize(
    "resolution, components, dimension",
    [
        (2.0, "rsn", 10),
        (2.0, "rsn", 20),
        (2.0, "rsn", 70),
        (2.0, "bm", 10),
        (2.0, "bm", 20),
        (2.0, "bm", 70),
    ],
)
def test_smith(
    resolution: float,
    components: str,
    dimension: int,
) -> None:
    """Test Smith maps.

    Parameters
    ----------
    resolution : float
        The parametrized resolution values.
    components : str
        The parametrized components values.
    dimension : int
        The parametrized dimension values.

    """
    maps = list_data(kind="maps")
    maps_name = f"Smith_{components}_{dimension}"
    assert maps_name in maps

    maps_file = f"{components}{dimension}.nii.gz"
    # Load maps
    img, label, img_path, space = load_data(
        kind="maps",
        name=maps_name,
        target_space="MNI152NLin6Asym",
        resolution=resolution,
    )
    assert img is not None
    assert img_path.name == maps_file
    assert space == "MNI152NLin6Asym"
    assert len(label) == dimension
    assert_array_equal(
        img.header["pixdim"][1:4],
        3 * [2.0],
    )


def test_retrieve_smith_incorrect_components() -> None:
    """Test retrieve Smith with incorrect components."""
    with pytest.raises(ValueError, match="The parameter `components`"):
        _retrieve_smith(
            components="abc",
            dimension=10,
        )


def test_retrieve_smith_incorrect_dimension() -> None:
    """Test retrieve Smith with incorrect dimension."""
    with pytest.raises(ValueError, match="The parameter `dimension`"):
        _retrieve_smith(
            components="rsn",
            dimension=100,
        )
