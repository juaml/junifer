"""Provide tests for markers on regions lost in resampling."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from collections.abc import Iterator
from importlib.util import find_spec
from pathlib import Path

import nibabel as nib
import numpy as np
import pytest

from junifer import markers
from junifer.data import deregister_data, register_data
from junifer.datareader import DefaultDataReader
from junifer.pipeline import WorkDirManager


COMPLEXITY_MARKERS = (
    "HurstExponent",
    "RangeEntropy",
    "RangeEntropyAUC",
    "MultiscaleEntropyAUC",
    "PermEntropy",
    "WeightedPermEntropy",
    "SampleEntropy",
)

skip_no_neurokit2 = pytest.mark.skipif(
    find_spec("neurokit2") is None, reason="requires neurokit2"
)


@pytest.fixture(scope="module")
def element(tmp_path_factory: pytest.TempPathFactory) -> Iterator[dict]:
    """Provide BOLD data where regions of the parcellations are lost.

    The parcellations are on a 1mm grid and the BOLD data on a 3mm grid,
    which does not sample their single-voxel regions:

    * ``LostRegion`` (and ``LostRegion2``, the same): regions ``a``, ``b``,
      ``lost``, ``c`` and ``d``.
    * ``OneRegionLeft``: regions ``kept``, ``lost`` and ``lost_too``.

    Parameters
    ----------
    tmp_path_factory : pytest.TempPathFactory
        The pytest factory for temporary directories.

    Yields
    ------
    dict
        The element data.

    """
    tmp_path = tmp_path_factory.mktemp("lost_regions")
    # Voxels 0, 3, 6, ... are sampled by the 3mm grid, 7 and 13 are not
    lost_region = np.zeros((24, 24, 24), dtype=np.int16)
    lost_region[0:12, 0:12] = 1
    lost_region[12:24, 0:12] = 2
    lost_region[7, 13, 7] = 3
    lost_region[0:12, 15:24] = 4
    lost_region[12:24, 15:24] = 5
    one_region_left = np.zeros((24, 24, 24), dtype=np.int16)
    one_region_left[0:12, 0:12] = 1
    one_region_left[7, 13, 7] = 2
    one_region_left[13, 7, 7] = 3
    for name, data, labels in (
        ("LostRegion", lost_region, ["a", "b", "lost", "c", "d"]),
        ("LostRegion2", lost_region, ["a", "b", "lost", "c", "d"]),
        ("OneRegionLeft", one_region_left, ["kept", "lost", "lost_too"]),
    ):
        path = tmp_path / f"{name}.nii.gz"
        nib.save(nib.Nifti1Image(data, np.eye(4)), path)
        register_data(
            kind="parcellation",
            name=name,
            parcellation_path=path,
            parcels_labels=labels,
            space="MNI152NLin6Asym",
        )
    # Random walks, so all the measures are defined
    rng = np.random.default_rng(0)
    bold = rng.normal(size=(8, 8, 8, 120)).cumsum(axis=-1) + 1000
    bold_img = nib.Nifti1Image(
        bold.astype(np.float32), np.diag([3.0, 3.0, 3.0, 1.0])
    )
    bold_img.header.set_xyzt_units("mm", "sec")
    bold_path = tmp_path / "bold.nii.gz"
    nib.save(bold_img, bold_path)
    yield DefaultDataReader().fit_transform(
        {"BOLD": {"path": bold_path, "space": "MNI152NLin6Asym"}}
    )
    for name in ("LostRegion", "LostRegion2", "OneRegionLeft"):
        deregister_data(kind="parcellation", name=name)


def _case(name: str, params: dict, feature: str, nan: list) -> object:
    """Get a test case.

    Parameters
    ----------
    name : str
        The name of the marker class.
    params : dict
        The parameters of the marker.
    feature : str
        The name of the feature to check.
    nan : list
        The values that are NaN.

    Returns
    -------
    object
        The test case, named after the parcellation, marker and feature.
        Complexity markers are skipped if neurokit2 is not installed.

    """
    parcellation = params.get("parcellation", params.get("parcellation_one"))
    return pytest.param(
        name,
        params,
        feature,
        nan,
        marks=skip_no_neurokit2 if name in COMPLEXITY_MARKERS else (),
        id=f"{parcellation}-{name}-{feature}",
    )


# Whether the values are NaN for LostRegion, whose 3rd region is lost
REGIONS = [False, False, True, False, False]
# For connectivity, a region pair is NaN if one of the regions is lost
PAIRS = [[r or c for c in REGIONS] for r in REGIONS]
# For edge-centric FC, the edges are the region pairs (lower triangle)
EDGES = [r or c for i, r in enumerate(REGIONS) for c in REGIONS[:i]]
EDGE_PAIRS = [[r or c for c in EDGES] for r in EDGES]


@pytest.mark.parametrize(
    "name, params, feature, nan",
    [
        _case(
            "ParcelAggregation",
            {"parcellation": "LostRegion", "method": "mean", "on": "BOLD"},
            "aggregation",
            [REGIONS] * 120,
        ),
        _case(
            "FunctionalConnectivityParcels",
            {"parcellation": "LostRegion"},
            "functional_connectivity",
            PAIRS,
        ),
        _case(
            "EdgeCentricFCParcels",
            {"parcellation": "LostRegion"},
            "functional_connectivity",
            EDGE_PAIRS,
        ),
        _case(
            "CrossParcellationFC",
            {
                "parcellation_one": "LostRegion",
                "parcellation_two": "LostRegion2",
            },
            "functional_connectivity",
            PAIRS,
        ),
        _case(
            "ReHoParcels",
            {"parcellation": "LostRegion", "using": "junifer"},
            "reho",
            [REGIONS],
        ),
        _case(
            "ALFFParcels",
            {"parcellation": "LostRegion", "using": "junifer"},
            "alff",
            [REGIONS],
        ),
        _case(
            "ALFFParcels",
            {"parcellation": "LostRegion", "using": "junifer"},
            "falff",
            [REGIONS],
        ),
        _case(
            "TemporalSNRParcels",
            {"parcellation": "LostRegion"},
            "tsnr",
            [REGIONS],
        ),
        # Computed with the edges with data
        _case(
            "RSSETSMarker",
            {"parcellation": "LostRegion"},
            "rss_ets",
            [[False]] * 120,
        ),
        *[
            _case(
                name, {"parcellation": "LostRegion"}, "complexity", [REGIONS]
            )
            for name in COMPLEXITY_MARKERS
        ],
        # Only the kept region with itself
        _case(
            "FunctionalConnectivityParcels",
            {"parcellation": "OneRegionLeft"},
            "functional_connectivity",
            [[False, True, True], [True, True, True], [True, True, True]],
        ),
        # All the edges have a lost region
        _case(
            "EdgeCentricFCParcels",
            {"parcellation": "OneRegionLeft"},
            "functional_connectivity",
            [[True] * 3] * 3,
        ),
        # No edges with data
        _case(
            "RSSETSMarker",
            {"parcellation": "OneRegionLeft"},
            "rss_ets",
            [[True]] * 120,
        ),
        *[
            _case(
                name,
                {"parcellation": "OneRegionLeft"},
                "complexity",
                [[False, True, True]],
            )
            for name in COMPLEXITY_MARKERS
        ],
    ],
)
def test_lost_regions(
    tmp_path: Path,
    element: dict,
    name: str,
    params: dict,
    feature: str,
    nan: list,
) -> None:
    """Test markers on regions lost in resampling.

    The lost regions have no data (NaN), and the other regions are not
    affected.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    element : dict
        The element data.
    name : str
        The parametrized name of the marker class.
    params : dict
        The parametrized parameters of the marker.
    feature : str
        The parametrized name of the feature to check.
    nan : list
        The parametrized values that are NaN.

    """
    if name in COMPLEXITY_MARKERS:
        from junifer.markers import complexity

        marker = getattr(complexity, name)(**params)
    else:
        marker = getattr(markers, name)(**params)
    WorkDirManager().workdir = tmp_path
    with pytest.warns(RuntimeWarning, match=r"region\(s\) .* have no voxels"):
        # Copy the data, as some markers change their input
        out = marker.fit_transform({"BOLD": dict(element["BOLD"])})
    data = np.asarray(out["BOLD"][feature]["data"], dtype=float)
    assert np.array_equal(np.isnan(data), nan)
