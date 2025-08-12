"""Provide tests for maps."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

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
from junifer.pipeline.utils import _check_ants
from junifer.testing.datagrabbers import PartlyCloudyTestingDataGrabber


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
    maps, labels, maps_path, _ = load_data(
        kind="maps",
        name="Smith_rsn_10",
        target_space="MNI152NLin6Asym",
    )
    assert maps is not None

    # Test wrong number of labels
    register_data(
        kind="maps",
        name="WrongLabels",
        maps_path=maps_path,
        maps_labels=labels[:5],
        space="MNI152NLin6Asym",
    )
    with pytest.raises(ValueError, match=r"has 10 regions but 5"):
        load_data(
            kind="maps",
            name="WrongLabels",
            target_space="MNI152NLin6Asym",
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
        element_data = DefaultDataReader().fit_transform(element)
        bold = element_data["BOLD"]
        bold_img = bold["data"]
        # Get tailored coordinates
        tailored_maps, tailored_labels = get_data(
            kind="maps", names="Smith_rsn_10", target_data=bold
        )

        # Check shape with original element data
        assert tailored_maps.shape[:3] == bold_img.shape[:3]

        # Get raw maps
        raw_maps, raw_labels, _, _ = load_data(
            kind="maps", name="Smith_rsn_10", target_space="MNI152NLin6Asym"
        )
        # Tailored and raw shape should be same
        assert tailored_maps.shape[:3] == raw_maps.shape[:3]
        assert tailored_labels == raw_labels


@pytest.mark.skipif(
    _check_ants() is False, reason="requires ANTs to be in PATH"
)
def test_get_different_space() -> None:
    """Test tailored maps fetch in different space."""
    with PartlyCloudyTestingDataGrabber() as dg:
        element = dg["sub-01"]
        element_data = DefaultDataReader().fit_transform(element)
        bold = element_data["BOLD"]
        bold_img = bold["data"]
        # Get tailored coordinates
        tailored_maps, tailored_labels = get_data(
            kind="maps", names="Smith_rsn_10", target_data=bold
        )

        # Check shape with original element data
        assert tailored_maps.shape[:3] == bold_img.shape[:3]

        # Get raw maps
        raw_maps, raw_labels, _, _ = load_data(
            kind="maps",
            name="Smith_rsn_10",
            target_space="MNI152NLin2009cAsym",
        )
        # Tailored and raw should not be same
        assert tailored_maps.shape[:3] != raw_maps.shape[:3]
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
