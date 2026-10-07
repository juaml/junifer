"""Provide tests for PartlyCloudyTestingDataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

import nibabel as nib
import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_array_equal
from pandas.testing import assert_frame_equal

from junifer.testing.datagrabbers import PartlyCloudyTestingDataGrabber


pytestmark = pytest.mark.external


def test_PartlyCloudyTestingDataGrabber() -> None:
    """Test PartlyCloudyTestingDataGrabber."""
    expected_elements = [
        "sub-01",
        "sub-02",
        "sub-03",
        "sub-04",
        "sub-05",
        "sub-06",
        "sub-07",
        "sub-08",
        "sub-09",
        "sub-10",
    ]
    with PartlyCloudyTestingDataGrabber() as dg:
        all_elements = dg.get_elements()
        assert set(all_elements) == set(expected_elements)
        out = dg["sub-01"]
        assert "BOLD" in out
        assert out["BOLD"]["path"].exists()
        assert out["BOLD"]["path"].is_file()

        assert "confounds" in out["BOLD"]
        assert out["BOLD"]["confounds"]["path"].exists()
        assert out["BOLD"]["confounds"]["path"].is_file()
        assert "format" in out["BOLD"]["confounds"]
        assert "fmriprep" == out["BOLD"]["confounds"]["format"]

    with PartlyCloudyTestingDataGrabber(reduce_confounds=False) as dg:
        out = dg["sub-01"]
        assert "format" in out["BOLD"]["confounds"]
        assert "fmriprep" == out["BOLD"]["confounds"]["format"]


@pytest.mark.parametrize("reduce_confounds", [True, False])
def test_PartlyCloudyTestingDataGrabber_n_timepoints(
    reduce_confounds: bool,
) -> None:
    """Test PartlyCloudyTestingDataGrabber with fewer timepoints.

    Parameters
    ----------
    reduce_confounds : bool
        The parametrized confounds reduction.

    """
    with PartlyCloudyTestingDataGrabber(
        reduce_confounds=reduce_confounds
    ) as dg:
        full = dg["sub-01"]["BOLD"]
    with PartlyCloudyTestingDataGrabber(
        reduce_confounds=reduce_confounds, n_timepoints=50
    ) as dg:
        out = dg["sub-01"]["BOLD"]

    full_img = nib.load(full["path"])
    out_img = nib.load(out["path"])
    assert out_img.shape == (*full_img.shape[:3], 50)
    assert_array_equal(
        np.asanyarray(out_img.dataobj),
        np.asanyarray(full_img.dataobj[..., :50]),
    )

    full_confounds = pd.read_csv(full["confounds"]["path"], sep="\t")
    out_confounds = pd.read_csv(out["confounds"]["path"], sep="\t")
    assert out_confounds.shape == (50, full_confounds.shape[1])
    assert_frame_equal(out_confounds, full_confounds.iloc[:50])
