"""Provide tests for base marker."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from collections.abc import Callable
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd
import pytest
from nilearn.image import get_data

from junifer.datagrabber import DataType
from junifer.markers import BaseMarker
from junifer.storage import StorageType


def test_base_marker_abstractness() -> None:
    """Test BaseMarker is abstract base class."""
    with pytest.raises(TypeError, match=r"abstract"):
        BaseMarker(on=["BOLD"])  # type: ignore


def test_base_marker_subclassing() -> None:
    """Test proper subclassing of BaseMarker."""

    # Create concrete class
    class MyBaseMarker(BaseMarker):
        _MARKER_INOUT_MAPPINGS = {  # noqa: RUF012
            DataType.BOLD: {
                "feat_1": StorageType.Timeseries,
            },
        }

        parameter: int = 1

        def compute(self, input, extra_input):
            return {
                "feat_1": {
                    "data": "data",
                    "col_names": ["columns"],
                },
            }

    with pytest.raises(ValueError, match=r"cannot be computed on \['T1w'\]"):
        MyBaseMarker(on=["BOLD", "T1w"])

    # Create input for marker
    input_ = {
        "BOLD": {
            "path": ".",
            "data": "data",
            "meta": {
                "datagrabber": "dg",
                "element": "elem",
                "datareader": "dr",
            },
        },
    }
    marker = MyBaseMarker(on=["BOLD"])

    with pytest.raises(ValueError, match="not have the required data"):
        marker.validate_input(["T1w"])

    assert marker.validate_input(["BOLD", "Other"]) == ["BOLD"]

    output = marker.fit_transform(input=input_)  # process
    # Check output
    assert "BOLD" in output
    assert "data" in output["BOLD"]["feat_1"]
    assert "col_names" in output["BOLD"]["feat_1"]

    assert "meta" in output["BOLD"]["feat_1"]
    meta = output["BOLD"]["feat_1"]["meta"]
    assert "datagrabber" in meta
    assert "element" in meta
    assert "datareader" in meta
    assert "marker" in meta
    assert "name" in meta["marker"]
    assert "parameter" in meta["marker"]
    assert meta["marker"]["parameter"] == 1

    # Check attributes
    assert marker.name == "MyBaseMarker"

    # Add one extra input that will not be used to compute
    input_ = {
        "BOLD": {
            "path": ".",
            "data": "data",
            "meta": {
                "datagrabber": "dg",
                "element": "elem",
                "datareader": "dr",
            },
        },
        "T2": {
            "path": ".",
            "data": "data",
            "meta": {
                "datagrabber": "dg",
                "element": "elem",
                "datareader": "dr",
            },
        },
    }
    marker = MyBaseMarker(on=["BOLD"])
    output = marker.fit_transform(input=input_)  # process
    # Check output
    assert "BOLD" in output
    assert "T2" not in output


def _fit(change: Callable, tmp_path: Path) -> dict:
    """Fit a marker that applies a function to its input.

    Parameters
    ----------
    change : callable
        The function, called with the input and the extra input.
    tmp_path : pathlib.Path
        The path to the test directory.

    Returns
    -------
    dict
        The output of the marker.

    """

    class Marker(BaseMarker):
        _MARKER_INOUT_MAPPINGS = {  # noqa: RUF012
            DataType.BOLD: {"feat": StorageType.Vector},
        }

        def compute(self, input, extra_input=None):
            change(input, extra_input)
            return {"feat": {"data": np.zeros((1, 1)), "col_names": ["x"]}}

    marker = Marker(on=["BOLD"], name="marker")
    return marker.fit_transform(input=_input(tmp_path))


def _input(tmp_path: Path) -> dict:
    """Get input data with the types of values the markers check.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    Returns
    -------
    dict
        The input data.

    """
    # Non-integer values, which change when read as float32
    values = np.full((2, 2, 2), 0.1)
    # File-backed image, with its data cached
    t1w_path = tmp_path / "t1w.nii.gz"
    nib.save(nib.Nifti1Image(values, np.eye(4)), t1w_path)
    t1w = nib.load(t1w_path)
    t1w.get_fdata()
    # File-backed image, without its data loaded
    mask_path = tmp_path / "mask.nii.gz"
    nib.save(nib.Nifti1Image(values, np.eye(4)), mask_path)
    meta = {
        "datagrabber": "dg",
        "element": {"subject": "sub-01"},
        "dependencies": {"numpy"},
    }
    return {
        "BOLD": {
            "path": tmp_path / "bold.nii.gz",
            # In-memory image
            "data": nib.Nifti1Image(np.full((2, 2, 2, 3), 0.1), np.eye(4)),
            "array": np.arange(4.0),
            "mask": nib.load(mask_path),
            "confounds": {"data": pd.DataFrame({"a": [1.0, 2.0, 3.0]})},
            "meta": meta,
        },
        "T1w": {"path": t1w_path, "data": t1w, "meta": meta.copy()},
        "Warp": [{"src": "MNI", "dst": "native"}],
    }


def replace_value(input: dict, extra_input: dict) -> None:
    """Replace a value."""
    input["data"] = "new"


def add_nested_value(input: dict, extra_input: dict) -> None:
    """Add a value to a nested dictionary."""
    input["meta"]["new"] = 1


def remove_nested_value(input: dict, extra_input: dict) -> None:
    """Remove the values of a nested dictionary."""
    input["meta"]["element"].clear()


def remove_value(input: dict, extra_input: dict) -> None:
    """Remove a value."""
    del input["path"]


def change_array(input: dict, extra_input: dict) -> None:
    """Change an array in place."""
    input["array"][0] = 9.0


def reshape_array(input: dict, extra_input: dict) -> None:
    """Change the shape of an array in place."""
    input["array"].shape = (2, 2)


def change_array_dtype(input: dict, extra_input: dict) -> None:
    """Change the dtype of an array in place."""
    input["array"].dtype = np.int64


def change_image_data(input: dict, extra_input: dict) -> None:
    """Change the data of an in-memory image in place."""
    np.asarray(input["data"].dataobj)[0, 0, 0, 0] = 9.0


def change_image_affine(input: dict, extra_input: dict) -> None:
    """Change the affine of an image in place."""
    input["data"].affine[0, 3] = 9.0


def change_dataframe(input: dict, extra_input: dict) -> None:
    """Change a column of a data frame in place."""
    input["confounds"]["data"]["a"] = 0.0


def rename_dataframe_column(input: dict, extra_input: dict) -> None:
    """Rename a column of a data frame in place."""
    input["confounds"]["data"].rename(columns={"a": "b"}, inplace=True)


def change_list_item(input: dict, extra_input: dict) -> None:
    """Change an item of a list."""
    extra_input["Warp"][0]["dst"] = "MNI"


def append_to_list(input: dict, extra_input: dict) -> None:
    """Append an item to a list."""
    extra_input["Warp"].append({})


def clear_set(input: dict, extra_input: dict) -> None:
    """Remove the items of a set."""
    input["meta"]["dependencies"].clear()


def change_cached_image_data(input: dict, extra_input: dict) -> None:
    """Change the cached data of an image of the extra input."""
    extra_input["T1w"]["data"].get_fdata()[0, 0, 0] = 9.0


def change_image_data_read_with_nilearn(
    input: dict, extra_input: dict
) -> None:
    """Change the data of an image, after loading it with nilearn."""
    get_data(input["mask"])[0, 0, 0] = 9.0


def change_image_data_read_with_nibabel(
    input: dict, extra_input: dict
) -> None:
    """Change the data of an image, after loading it with nibabel."""
    input["mask"].get_fdata()[0, 0, 0] = 9.0


# The changes of the input and the paths of the data they change
_CHANGES = {
    replace_value: "BOLD.data",
    add_nested_value: "BOLD.meta.new",
    remove_nested_value: "BOLD.meta.element.subject",
    remove_value: "BOLD.path",
    change_array: "BOLD.array",
    reshape_array: "BOLD.array",
    change_array_dtype: "BOLD.array",
    change_image_data: "BOLD.data",
    change_image_affine: "BOLD.data",
    change_dataframe: "BOLD.confounds.data",
    rename_dataframe_column: "BOLD.confounds.data",
    change_list_item: "Warp.0.dst",
    append_to_list: "Warp.1",
    clear_set: "BOLD.meta.dependencies",
    change_cached_image_data: "T1w.data",
    change_image_data_read_with_nilearn: "BOLD.mask",
    change_image_data_read_with_nibabel: "BOLD.mask",
}


@pytest.mark.parametrize(
    "change, changed",
    _CHANGES.items(),
    ids=[change.__name__ for change in _CHANGES],
)
def test_base_marker_input_changed(
    tmp_path: Path, change: Callable, changed: str
) -> None:
    """Test markers cannot change their input data.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    change : callable
        The parametrized change of the input.
    changed : str
        The parametrized path of the changed data.

    """
    with pytest.raises(RuntimeError, match=rf"marker changed .*{changed}"):
        _fit(change, tmp_path)


def test_base_marker_input_not_changed(tmp_path: Path) -> None:
    """Test markers that only read their input data.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """

    def read(input: dict, extra_input: dict) -> None:
        input["data"].get_fdata()
        float(np.sum(input["array"]))
        float(input["confounds"]["data"]["a"].sum())
        # Replace the cached float64 data with float32
        extra_input["T1w"]["data"].get_fdata(dtype=np.float32)
        # Cache float32 data
        input["mask"].get_fdata(dtype=np.float32)
        get_data(input["mask"])
        set(input["meta"]["dependencies"])
        [warp["dst"] for warp in extra_input["Warp"]]

    out = _fit(read, tmp_path)
    assert "feat" in out["BOLD"]
