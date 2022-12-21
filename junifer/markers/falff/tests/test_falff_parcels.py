"""Provide test for parcel-aggregated (f)ALFF."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

import pytest
from numpy.testing import assert_array_equal
from scipy.stats import pearsonr

from junifer.datareader import DefaultDataReader
from junifer.markers.falff import AmplitudeLowFrequencyFluctuationParcels
from junifer.pipeline.utils import _check_afni
from junifer.storage import SQLiteFeatureStorage
from junifer.testing.datagrabbers import PartlyCloudyTestingDataGrabber
from junifer.utils import logger


_PARCELLATION = "Schaefer100x7"


def test_AmplitudeLowFrequencyFluctuationParcels_python() -> None:
    """Test AmplitudeLowFrequencyFluctuationParcels using python."""
    # Get the SPM auditory data:

    with PartlyCloudyTestingDataGrabber() as dg:
        input = dg["sub-01"]

    input = DefaultDataReader().fit_transform(input)
    # Create ParcelAggregation object
    marker = AmplitudeLowFrequencyFluctuationParcels(
        parcellation=_PARCELLATION,
        method="mean",
        use_afni=False,
        fractional=False,
    )
    python_values = marker.fit_transform(input)["BOLD"]["data"]

    assert marker.use_afni is False
    assert python_values.ndim == 2
    assert python_values.shape == (1, 100)


@pytest.mark.skipif(
    _check_afni() is False, reason="requires afni to be in PATH"
)
def test_AmplitudeLowFrequencyFluctuationParcels_afni() -> None:
    """Test AmplitudeLowFrequencyFluctuationParcels using afni."""
    # Get the SPM auditory data:
    with PartlyCloudyTestingDataGrabber() as dg:
        input = dg["sub-01"]

    input = DefaultDataReader().fit_transform(input)
    # Create ParcelAggregation object
    marker = AmplitudeLowFrequencyFluctuationParcels(
        parcellation=_PARCELLATION,
        method="mean",
        use_afni=True,
        fractional=False,
    )
    assert marker.use_afni is True
    afni_values = marker.fit_transform(input)["BOLD"]["data"]

    assert afni_values.ndim == 2
    assert afni_values.shape == (1, 100)

    # Again, should be blazing fast
    marker = AmplitudeLowFrequencyFluctuationParcels(
        parcellation=_PARCELLATION, method="mean", fractional=False
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
def test_AmplitudeLowFrequencyFluctuationParcels_python_vs_afni(
    fractional: bool,
) -> None:
    """Test AmplitudeLowFrequencyFluctuationParcels using python.

    Parameters
    ----------
    factional : bool
        Whether to compute fractional ALFF or not.
    """

    with PartlyCloudyTestingDataGrabber() as dg:
        input = dg["sub-01"]

    input = DefaultDataReader().fit_transform(input)
    # Create ParcelAggregation object
    marker_python = AmplitudeLowFrequencyFluctuationParcels(
        parcellation=_PARCELLATION,
        method="mean",
        use_afni=False,
        fractional=fractional,
    )
    python_values = marker_python.fit_transform(input)["BOLD"]["data"]

    assert marker_python.use_afni is False
    assert python_values.ndim == 2
    assert python_values.shape == (1, 100)

    marker_afni = AmplitudeLowFrequencyFluctuationParcels(
        parcellation=_PARCELLATION,
        method="mean",
        use_afni=True,
        fractional=fractional,
    )
    afni_values = marker_afni.fit_transform(input)["BOLD"]["data"]

    assert marker_afni.use_afni is True
    assert afni_values.ndim == 2
    assert afni_values.shape == (1, 100)

    r, p = pearsonr(python_values[0], afni_values[0])
    logger.info(f"Correlation between python and afni: {r} (p={p})")
    assert r > 0.99


def test_AmplitudeLowFrequencyFluctuationParcels_storage(
    tmp_path: Path,
) -> None:
    """Test AmplitudeLowFrequencyFluctuationParcels storage.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    """
    with PartlyCloudyTestingDataGrabber() as dg:
        # Use first subject
        input = dg["sub-01"]
        input = DefaultDataReader().fit_transform(input)
        # Create ParcelAggregation object
        marker = AmplitudeLowFrequencyFluctuationParcels(
            parcellation=_PARCELLATION,
            method="mean",
            use_afni=False,
            fractional=True,
        )
        storage = SQLiteFeatureStorage(tmp_path / "alff_parcels.sqlite")

        # Fit transform marker on data with storage
        marker.fit_transform(
            input=input,
            storage=storage,
        )
