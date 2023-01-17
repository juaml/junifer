"""Provide test for sample entropy."""

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
from junifer.markers.complexity.sample_entropy import SampleEntropy
from junifer.storage import SQLiteFeatureStorage
from junifer.testing.datagrabbers import SPMAuditoryTestingDatagrabber


# Set parcellation
PARCELLATION = "Schaefer100x17"


def test_compute() -> None:
    """Test SampleEntropy compute()."""
    with SPMAuditoryTestingDatagrabber() as dg:
        # Fetch element
        out = dg["sub001"]
        # Load BOLD image
        niimg = image.load_img(str(out["BOLD"]["path"].absolute()))
        # Create input data
        input_dict = {"data": niimg, "path": out["BOLD"]["path"]}

        # Compute the SampleEntropy marker
        feature_map = SampleEntropy(parcellation=PARCELLATION)
        new_out = feature_map.compute(input_dict)

        # Load parcellation
        test_parcellation, _, _ = load_parcellation(PARCELLATION)

        # Compute the NiftiLabelsMasker
        test_masker = NiftiLabelsMasker(test_parcellation)
        test_ts = test_masker.fit_transform(niimg)

        # Assert the dimension of timeseries
        _, n_roi = test_ts.shape
        assert n_roi == len(new_out["data"])


def test_get_output_type() -> None:
    """Test SampleEntropy get_output_type()."""
    tmp = SampleEntropy(parcellation=PARCELLATION)
    input_list = ["BOLD"]
    input_list = tmp.get_output_type(input_list)
    assert len(input_list) == 1
    assert input_list[0] in ["matrix"]


def test_store(tmp_path: Path) -> None:
    """Test SampleEntropy store().

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
        # Compute the SampleEntropy measure
        feature_map = SampleEntropy(parcellation=PARCELLATION)
        # Create storage
        storage = SQLiteFeatureStorage(
            uri=str((tmp_path / "test.db").absolute()),
            single_output=True,
        )
        # Store
        feature_map.fit_transform(input=input_dict, storage=storage)
