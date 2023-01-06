"""Provide test for root sum of squares of edgewise timeseries."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
#          Nicolás Nieto <n.nieto@fz-juelich.de>
#          Sami Hamdan <s.hamdan@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
#          Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
# License: AGPL

from pathlib import Path

from nilearn import image
from nilearn.maskers import NiftiLabelsMasker

from junifer.data import load_parcellation
from junifer.markers.complexity.range_entropy import RangeEntropy
from junifer.storage import SQLiteFeatureStorage
from junifer.testing.datagrabbers import SPMAuditoryTestingDatagrabber


# Set parcellation
PARCELLATION = "Schaefer100x17"


def test_compute() -> None:
    """Test RangeEntropy compute()."""
    with SPMAuditoryTestingDatagrabber() as dg:
        # Fetch element
        out = dg["sub001"]
        # Load BOLD image
        niimg = image.load_img(str(out["BOLD"]["path"].absolute()))
        # Create input data
        input_dict = {"data": niimg, "path": out["BOLD"]["path"]}

        # Compute the RangeEntropy marker
        rangeen_b = RangeEntropy(parcellation=PARCELLATION)
        new_out = rangeen_b.compute(input_dict)

        # Load parcellation
        test_parcellation, _, _ = load_parcellation(PARCELLATION)

        # Compute the NiftiLabelsMasker
        test_masker = NiftiLabelsMasker(test_parcellation)
        test_ts = test_masker.fit_transform(niimg)

        # Assert the dimension of timeseries
        _, n_roi = test_ts.shape
        assert n_roi == len(new_out["data"])


def test_get_output_type() -> None:
    """Test RangeEntropy get_output_type()."""
    hurst = RangeEntropy(parcellation=PARCELLATION)
    input_list = ["BOLD"]
    input_list = hurst.get_output_type(input_list)
    assert len(input_list) == 1
    assert input_list[0] in ["matrix"]


def test_store(tmp_path: Path) -> None:
    """Test RangeEntropy store().

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    with SPMAuditoryTestingDatagrabber() as dg:
        # Fetch element
        out = dg["sub001"]
        # Load BOLD image
        niimg = image.load_img(str(out["BOLD"]["path"].absolute()))
        input_dict = {"data": niimg, "path": out["BOLD"]["path"]}
        # Compute the RangeEntropy measure
        rangeen_b = RangeEntropy(parcellation=PARCELLATION)
        # Create storage
        storage = SQLiteFeatureStorage(
            uri=str((tmp_path / "test.db").absolute()),
            single_output=True,
        )
        # Store
        rangeen_b.fit_transform(input=input_dict, storage=storage)
