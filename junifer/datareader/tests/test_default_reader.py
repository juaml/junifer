"""Provide tests for default data reader."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

import nibabel as nib
import pandas as pd
import pytest
from nibabel import testing as nib_testing
from numpy.testing import assert_array_equal
from pandas.testing import assert_frame_equal

from junifer.datareader import DefaultDataReader


@pytest.mark.parametrize(
    "type_", [["T1w", "BOLD", "T2", "dwi"], [], ["whatever"]]
)
def test_validation(type_) -> None:
    """Test validating input/output.

    Parameters
    ----------
    type_ : list of str or str or None
        The parametrized type_ of data.

    """
    reader = DefaultDataReader()
    assert reader.validate_input(type_) is None
    assert reader.get_output_type(type_) == type_
    assert reader.validate(type_) == type_


def test_meta() -> None:
    """Test reader metadata."""
    reader = DefaultDataReader()

    nib_data_path = Path(nib_testing.data_path)
    t_path = nib_data_path / "example4d.nii.gz"
    input = {"BOLD": {"path": t_path}}
    output = reader.fit_transform(input)
    assert "meta" in output["BOLD"]
    meta = output["BOLD"]["meta"]
    assert "datareader" in meta
    assert "class" in meta["datareader"]
    assert meta["datareader"]["class"] == "DefaultDataReader"


@pytest.mark.parametrize(
    "fname", ["example4d.nii.gz", "reoriented_anat_moved.nii"]
)
def test_read_nifti(fname: str) -> None:
    """Test reading NIFTI files.

    Parameters
    ----------
    fname : str
        The parametrized NIfTI file names for testing.

    """
    reader = DefaultDataReader()
    nib_data_path = Path(nib_testing.data_path)

    t_path = nib_data_path / fname

    input = {"BOLD": {"path": t_path}}
    output = reader.fit_transform(input)

    assert isinstance(output, dict)
    assert "BOLD" in output
    assert isinstance(output["BOLD"], dict)
    assert "path" in output["BOLD"]
    assert "data" in output["BOLD"]

    read_img = output["BOLD"]["data"]

    t_read_img = nib.load(t_path)
    assert_array_equal(read_img.get_fdata(), t_read_img.get_fdata())

    input = {"BOLD": {"path": t_path.as_posix()}}
    output2 = reader.fit_transform(input)
    assert output["BOLD"]["path"] == output2["BOLD"]["path"]


def test_read_unknown() -> None:
    """Test (not) reading unknown files."""
    reader = DefaultDataReader()
    nib_data_path = Path(nib_testing.data_path)

    anat_path = nib_data_path / "reoriented_anat_moved.nii"
    whatever_path = nib_data_path / "unexistent.unkwnownextension"

    input = {"anat": {"path": anat_path}, "whatever": {"path": whatever_path}}
    output = reader.fit_transform(input)

    assert isinstance(output, dict)
    assert "anat" in output
    assert isinstance(output["anat"], dict)
    assert "path" in output["anat"]
    assert isinstance(output["anat"]["path"], Path)
    assert "data" in output["anat"]
    assert output["anat"]["data"] is not None

    assert isinstance(output["whatever"], dict)
    assert "path" in output["whatever"]
    assert isinstance(output["whatever"]["path"], Path)
    assert "data" in output["whatever"]
    assert output["whatever"]["data"] is None

    input = {"whatever": {"nopath": whatever_path}}
    with pytest.warns(RuntimeWarning, match="does not provide a path"):
        reader.fit_transform(input)


def test_read_csv(tmp_path: Path) -> None:
    """Test reading CSV files.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    d = {"col1": [1, 2, 3, 4, 5], "col2": [3, 4, 5, 6, 7]}
    df = pd.DataFrame(d)

    df.to_csv(tmp_path / "test_read_csv.csv")

    reader = DefaultDataReader()
    input = {"csv": {"path": tmp_path / "test_read_csv.csv"}}
    output = reader.fit_transform(input)

    assert isinstance(output, dict)
    assert "csv" in output
    assert isinstance(output["csv"], dict)
    assert "path" in output["csv"]
    assert "data" in output["csv"]

    read_df = output["csv"]["data"][["col1", "col2"]]
    assert_frame_equal(df, read_df)

    df.to_csv(tmp_path / "test_read_csv.csv", sep=";")
    input = {"csv": {"path": tmp_path / "test_read_csv.csv"}}
    params = {"csv": {"sep": ";"}}
    output = reader.fit_transform(input, params=params)

    assert isinstance(output, dict)
    assert "csv" in output
    assert isinstance(output["csv"], dict)
    assert "path" in output["csv"]
    assert "data" in output["csv"]

    read_df = output["csv"]["data"][["col1", "col2"]]
    assert_frame_equal(df, read_df)

    df.to_csv(tmp_path / "test_read_csv.tsv", sep="\t")
    input = {"csv": {"path": tmp_path / "test_read_csv.tsv"}}
    output = reader.fit_transform(input)

    assert isinstance(output, dict)
    assert "csv" in output
    assert isinstance(output["csv"], dict)
    assert "path" in output["csv"]
    assert "data" in output["csv"]

    read_df = output["csv"]["data"][["col1", "col2"]]
    # Check if dataframes are equal
    assert_frame_equal(df, read_df)
