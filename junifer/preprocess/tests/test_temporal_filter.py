"""Provide tests for TemporalFilter."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import pytest

from junifer.datareader import DefaultDataReader
from junifer.preprocess import TemporalFilter
from junifer.testing.datagrabbers import PartlyCloudyTestingDataGrabber


pytestmark = pytest.mark.external


@pytest.mark.parametrize(
    "detrend, standardize, low_pass, high_pass, t_r, masks",
    (
        [
            True,
            "zscore_sample",
            None,
            None,
            None,
            None,
        ],
        [
            False,
            "zscore_sample",
            0.1,
            None,
            None,
            "compute_brain_mask",
        ],
        [
            True,
            None,
            None,
            0.08,
            None,
            ["compute_background_mask"],
        ],
        [
            False,
            "psc",
            None,
            None,
            2,
            None,
        ],
        [
            True,
            "zscore_sample",
            0.1,
            0.08,
            2,
            "compute_brain_mask",
        ],
    ),
)
def test_TemporalFilter(
    detrend: bool,
    standardize: str | None,
    low_pass: float | None,
    high_pass: float | None,
    t_r: float | None,
    masks: str | list[str] | None,
) -> None:
    """Test TemporalFilter.

    Parameters
    ----------
    detrend : bool
        The parametrized detrending flag.
    standardize : str or None
        The parametrized standardization strategy.
    low_pass : float or None
        The parametrized low pass value.
    high_pass : float or None
        The parametrized high pass value.
    t_r : float or None
        The parametrized repetition time.
    masks : str, list of str or None
        The parametrized mask.

    """
    with PartlyCloudyTestingDataGrabber() as dg:
        # Read data
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        # Preprocess data
        output = TemporalFilter(
            detrend=detrend,
            standardize=standardize,
            low_pass=low_pass,
            high_pass=high_pass,
            t_r=t_r,
            masks=masks,
        ).fit_transform(element_data)

        assert isinstance(output, dict)


@pytest.mark.parametrize("standardize", [True, False])
def test_TemporalFilter_standardize_bool(standardize: bool) -> None:
    """Test TemporalFilter error for boolean standardize.

    Parameters
    ----------
    standardize : bool
        The parametrized standardization flag.

    """
    with pytest.raises(ValueError, match="does not accept booleans"):
        TemporalFilter(standardize=standardize)
