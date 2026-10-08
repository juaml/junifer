"""Provide tests for markers on regions lost in resampling."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from collections.abc import Callable, Iterator
from importlib.util import find_spec
from pathlib import Path

import nibabel as nib
import numpy as np
import pytest

from junifer.data import deregister_data, register_data
from junifer.datareader import DefaultDataReader
from junifer.markers import (
    ALFFParcels,
    CrossParcellationFC,
    EdgeCentricFCParcels,
    FunctionalConnectivityParcels,
    ParcelAggregation,
    ReHoParcels,
    RSSETSMarker,
    TemporalSNRParcels,
)
from junifer.markers.base import BaseMarker
from junifer.pipeline import WorkDirManager


# Index of the lost region in the parcellation labels
LOST = 2
LABELS = ["a", "b", "lost", "c", "d"]

skip_no_neurokit2 = pytest.mark.skipif(
    find_spec("neurokit2") is None, reason="requires neurokit2"
)

COMPLEXITY_MARKERS = (
    "HurstExponent",
    "RangeEntropy",
    "RangeEntropyAUC",
    "MultiscaleEntropyAUC",
    "PermEntropy",
    "WeightedPermEntropy",
    "SampleEntropy",
)


@pytest.fixture(scope="module")
def element(tmp_path_factory: pytest.TempPathFactory) -> Iterator[dict]:
    """Provide BOLD data where a region of the parcellations is lost.

    The parcellations are on a 1mm grid and the BOLD data on a 3mm grid that
    does not sample their single-voxel regions: ``lost`` in ``LostRegion``
    and ``LostRegion2``, and ``lost`` and ``lost_too`` in ``OneRegionLeft``.

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
    parcellation = np.zeros((24, 24, 24), dtype=np.int16)
    parcellation[0:12, 0:12] = 1
    parcellation[12:24, 0:12] = 2
    # A single voxel, not sampled by the 3mm grid (voxels 0, 3, 6, ...)
    parcellation[7, 13, 7] = 3
    parcellation[0:12, 15:24] = 4
    parcellation[12:24, 15:24] = 5
    parcellation_path = tmp_path / "parcellation.nii.gz"
    nib.save(nib.Nifti1Image(parcellation, np.eye(4)), parcellation_path)
    for name in ("LostRegion", "LostRegion2"):
        register_data(
            kind="parcellation",
            name=name,
            parcellation_path=parcellation_path,
            parcels_labels=LABELS,
            space="MNI152NLin6Asym",
        )
    # Only one region with data
    one_region = np.zeros((24, 24, 24), dtype=np.int16)
    one_region[0:12, 0:12] = 1
    one_region[7, 13, 7] = 2
    one_region[13, 7, 7] = 3
    one_region_path = tmp_path / "one_region.nii.gz"
    nib.save(nib.Nifti1Image(one_region, np.eye(4)), one_region_path)
    register_data(
        kind="parcellation",
        name="OneRegionLeft",
        parcellation_path=one_region_path,
        parcels_labels=["kept", "lost", "lost_too"],
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


def _complexity(
    name: str, parcellation: str = "LostRegion"
) -> Callable[[], BaseMarker]:
    """Get a complexity marker, importing it only when needed.

    Parameters
    ----------
    name : str
        The name of the complexity marker.
    parcellation : str, optional
        The name of the parcellation (default "LostRegion").

    Returns
    -------
    callable
        The function to create the marker.

    """

    def make() -> BaseMarker:
        from junifer.markers import complexity

        return getattr(complexity, name)(parcellation=parcellation)

    return make


@pytest.mark.parametrize(
    "make_marker, feature, output",
    [
        pytest.param(
            lambda: ParcelAggregation(
                parcellation="LostRegion", method="mean", on="BOLD"
            ),
            "aggregation",
            "regions",
            id="ParcelAggregation",
        ),
        pytest.param(
            lambda: FunctionalConnectivityParcels(parcellation="LostRegion"),
            "functional_connectivity",
            "matrix",
            id="FunctionalConnectivityParcels",
        ),
        pytest.param(
            lambda: EdgeCentricFCParcels(parcellation="LostRegion"),
            "functional_connectivity",
            "edges",
            id="EdgeCentricFCParcels",
        ),
        pytest.param(
            lambda: CrossParcellationFC(
                parcellation_one="LostRegion", parcellation_two="LostRegion2"
            ),
            "functional_connectivity",
            "matrix",
            id="CrossParcellationFC",
        ),
        pytest.param(
            lambda: ReHoParcels(parcellation="LostRegion", using="junifer"),
            "reho",
            "regions",
            id="ReHoParcels",
        ),
        pytest.param(
            lambda: ALFFParcels(parcellation="LostRegion", using="junifer"),
            "alff",
            "regions",
            id="ALFFParcels-alff",
        ),
        pytest.param(
            lambda: ALFFParcels(parcellation="LostRegion", using="junifer"),
            "falff",
            "regions",
            id="ALFFParcels-falff",
        ),
        pytest.param(
            lambda: TemporalSNRParcels(parcellation="LostRegion"),
            "tsnr",
            "regions",
            id="TemporalSNRParcels",
        ),
        pytest.param(
            lambda: RSSETSMarker(parcellation="LostRegion"),
            "rss_ets",
            "no_nan",
            id="RSSETSMarker",
        ),
        *[
            pytest.param(
                _complexity(name),
                "complexity",
                "regions",
                marks=skip_no_neurokit2,
                id=name,
            )
            for name in COMPLEXITY_MARKERS
        ],
    ],
)
def test_lost_region(
    tmp_path: Path,
    element: dict,
    make_marker: Callable[[], BaseMarker],
    feature: str,
    output: str,
) -> None:
    """Test markers on a region lost in resampling.

    The lost region has no data (NaN), and the other regions are not
    affected.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    element : dict
        The element data.
    make_marker : callable
        The parametrized function to create the marker.
    feature : str
        The parametrized name of the feature to check.
    output : {"regions", "matrix", "edges", "no_nan"}
        The parametrized kind of output: one column per region, a region by
        region matrix, an edge by edge matrix, or a summary over all regions.

    """
    WorkDirManager().workdir = tmp_path
    # Copy the data, as some markers change their input
    with pytest.warns(RuntimeWarning, match=r"region\(s\) .* \['lost'\]"):
        out = make_marker().fit_transform({"BOLD": dict(element["BOLD"])})
    result = out["BOLD"][feature]
    nan = np.isnan(np.asarray(result["data"], dtype=float))
    if output == "regions":
        expected = np.zeros(nan.shape, dtype=bool)
        expected[:, LOST] = True
    elif output == "matrix":
        expected = np.zeros(nan.shape, dtype=bool)
        expected[LOST, :] = True
        expected[:, LOST] = True
    elif output == "edges":
        lost_edges = np.array(
            ["lost" in name.split("~") for name in result["col_names"]]
        )
        expected = lost_edges[:, np.newaxis] | lost_edges[np.newaxis, :]
    else:
        expected = np.zeros(nan.shape, dtype=bool)
    assert np.array_equal(nan, expected)


@pytest.mark.parametrize(
    "make_marker, feature, expected_values",
    [
        pytest.param(
            lambda: FunctionalConnectivityParcels(
                parcellation="OneRegionLeft"
            ),
            "functional_connectivity",
            # Only the connectivity of the kept region with itself
            np.array([[1, 0, 0], [0, 0, 0], [0, 0, 0]], dtype=bool),
            id="FunctionalConnectivityParcels",
        ),
        pytest.param(
            lambda: EdgeCentricFCParcels(parcellation="OneRegionLeft"),
            "functional_connectivity",
            # All the edges have a lost region
            np.zeros((3, 3), dtype=bool),
            id="EdgeCentricFCParcels",
        ),
        pytest.param(
            lambda: RSSETSMarker(parcellation="OneRegionLeft"),
            "rss_ets",
            # No edges with data
            np.zeros((120, 1), dtype=bool),
            id="RSSETSMarker",
        ),
        *[
            pytest.param(
                _complexity(name, parcellation="OneRegionLeft"),
                "complexity",
                np.array([[1, 0, 0]], dtype=bool),
                marks=skip_no_neurokit2,
                id=name,
            )
            for name in COMPLEXITY_MARKERS
        ],
    ],
)
def test_one_region_left(
    tmp_path: Path,
    element: dict,
    make_marker: Callable[[], BaseMarker],
    feature: str,
    expected_values: np.ndarray,
) -> None:
    """Test markers when a single region has data.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    element : dict
        The element data.
    make_marker : callable
        The parametrized function to create the marker.
    feature : str
        The parametrized name of the feature to check.
    expected_values : np.ndarray
        The parametrized mask of the values that are not NaN.

    """
    WorkDirManager().workdir = tmp_path
    with pytest.warns(RuntimeWarning, match=r"2 region\(s\)"):
        out = make_marker().fit_transform({"BOLD": dict(element["BOLD"])})
    data = np.asarray(out["BOLD"][feature]["data"], dtype=float)
    assert np.array_equal(~np.isnan(data), expected_values)
