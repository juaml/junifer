"""Provide test for sphere-aggregated (f)ALFF."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

import pytest
from numpy.testing import assert_array_equal
from scipy.stats import pearsonr

from junifer.datareader import DefaultDataReader
from junifer.markers.falff import ALFFSpheres
from junifer.pipeline import WorkDirManager
from junifer.pipeline.utils import _check_afni
from junifer.storage import SQLiteFeatureStorage
from junifer.testing.datagrabbers import PartlyCloudyTestingDataGrabber
from junifer.utils import logger


_COORDINATES = "DMNBuckner"


def test_ALFFSpheres_python(tmp_path: Path) -> None:
    """Test ALFFSpheres using python.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with PartlyCloudyTestingDataGrabber() as dg:
        input_ = dg["sub-01"]

    input_ = DefaultDataReader().fit_transform(input_)

    WorkDirManager().workdir = tmp_path
    marker = ALFFSpheres(
        coords=_COORDINATES,
        radius=5,
        method="mean",
        use_afni=False,
        fractional=False,
    )
    python_values = marker.fit_transform(input_)["BOLD"]["data"]

    assert marker.use_afni is False
    assert python_values.ndim == 2
    assert python_values.shape == (1, 6)


@pytest.mark.skipif(
    _check_afni() is False, reason="requires afni to be in PATH"
)
def test_ALFFSpheres_afni(tmp_path: Path) -> None:
    """Test ALFFSpheres using afni.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with PartlyCloudyTestingDataGrabber() as dg:
        input = dg["sub-01"]

    input = DefaultDataReader().fit_transform(input)

    WorkDirManager().workdir = tmp_path
    marker = ALFFSpheres(
        coords=_COORDINATES,
        radius=5,
        method="mean",
        use_afni=True,
        fractional=False,
    )
    assert marker.use_afni is True
    afni_values = marker.fit_transform(input)["BOLD"]["data"]

    assert afni_values.ndim == 2
    assert afni_values.shape == (1, 6)

    # Again, should be blazing fast
    marker = ALFFSpheres(
        coords=_COORDINATES,
        radius=5,
        method="mean",
        fractional=False,
    )
    assert marker.use_afni is None
    afni_values2 = marker.fit_transform(input)["BOLD"]["data"]
    assert marker.use_afni is True
    assert_array_equal(afni_values, afni_values2)


@pytest.mark.skipif(
    _check_afni() is False, reason="requires afni to be in PATH"
)
@pytest.mark.parametrize(
    "fractional", [True, False], ids=["fractional", "non-fractional"]
)
def test_ALFFSpheres_python_vs_afni(
    tmp_path: Path,
    fractional: bool,
) -> None:
    """Test ALFFSpheres python vs afni results.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    fractional : bool
        Whether to compute fractional ALFF or not.

    """
    with PartlyCloudyTestingDataGrabber() as dg:
        input_ = dg["sub-01"]

    input_ = DefaultDataReader().fit_transform(input_)

    WorkDirManager().workdir = tmp_path
    marker_python = ALFFSpheres(
        coords=_COORDINATES,
        radius=5,
        method="mean",
        use_afni=False,
        fractional=fractional,
    )
    python_values = marker_python.fit_transform(input_)["BOLD"]["data"]

    assert marker_python.use_afni is False
    assert python_values.ndim == 2
    assert python_values.shape == (1, 6)

    marker_afni = ALFFSpheres(
        coords=_COORDINATES,
        radius=5,
        method="mean",
        use_afni=True,
        fractional=fractional,
    )
    afni_values = marker_afni.fit_transform(input_)["BOLD"]["data"]

    assert marker_afni.use_afni is True
    assert afni_values.ndim == 2
    assert afni_values.shape == (1, 6)

    r, p = pearsonr(python_values[0], afni_values[0])
    logger.info(f"Correlation between python and afni: {r} (p={p})")
    assert r > 0.99


def test_ALFFSpheres_storage(
    tmp_path: Path,
) -> None:
    """Test ALFFSpheres storage.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with PartlyCloudyTestingDataGrabber() as dg:
        # Use first subject
        input_ = dg["sub-01"]
        input_ = DefaultDataReader().fit_transform(input_)
        WorkDirManager().workdir = tmp_path
        marker = ALFFSpheres(
            coords=_COORDINATES,
            radius=5,
            method="mean",
            use_afni=False,
            fractional=True,
        )
        storage = SQLiteFeatureStorage(tmp_path / "alff_parcels.sqlite")

        # Fit transform marker on data with storage
        marker.fit_transform(
            input=input_,
            storage=storage,
        )
