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


class _ReadingMarker(BaseMarker):
    """Marker that applies a function to its input."""

    _MARKER_INOUT_MAPPINGS = {  # noqa: RUF012
        DataType.BOLD: {"feat": StorageType.Vector},
    }

    def compute(self, input, extra_input=None):
        self._change(input, extra_input)  # type: ignore[attr-defined]
        return {"feat": {"data": np.zeros((1, 1)), "col_names": ["x"]}}


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
    # File-backed image, with its data cached
    t1w_path = tmp_path / "t1w.nii.gz"
    nib.save(nib.Nifti1Image(np.ones((2, 2, 2)), np.eye(4)), t1w_path)
    t1w = nib.load(t1w_path)
    t1w.get_fdata()
    # File-backed image, without its data loaded
    mask_path = tmp_path / "mask.nii.gz"
    nib.save(nib.Nifti1Image(np.ones((2, 2, 2)), np.eye(4)), mask_path)
    meta = {"datagrabber": "dg", "element": {"subject": "sub-01"}}
    return {
        "BOLD": {
            "path": tmp_path / "bold.nii.gz",
            # In-memory image
            "data": nib.Nifti1Image(np.ones((2, 2, 2, 3)), np.eye(4)),
            "array": np.arange(4.0),
            "mask": nib.load(mask_path),
            "confounds": {"data": pd.DataFrame({"a": [1.0, 2.0, 3.0]})},
            "meta": meta,
        },
        "T1w": {"path": t1w_path, "data": t1w, "meta": meta.copy()},
    }


def _set(input: dict, key: str, value: object) -> None:
    """Set a value of a dictionary."""
    input[key] = value


@pytest.mark.parametrize(
    "change, changed",
    [
        (lambda i, e: _set(i, "data", "new"), "BOLD.data"),
        (lambda i, e: _set(i["meta"], "new", 1), "BOLD.meta.new"),
        (
            lambda i, e: i["meta"]["element"].clear(),
            "BOLD.meta.element.subject",
        ),
        (lambda i, e: i.pop("path"), "BOLD.path"),
        (lambda i, e: i["array"].__setitem__(0, 9.0), "BOLD.array"),
        (
            lambda i, e: np.asarray(i["data"].dataobj).__setitem__(
                (0, 0, 0, 0), 9.0
            ),
            "BOLD.data",
        ),
        (lambda i, e: i["data"].affine.__setitem__((0, 3), 9.0), "BOLD.data"),
        (
            lambda i, e: i["confounds"]["data"].__setitem__("a", 0.0),
            "BOLD.confounds.data",
        ),
        (
            lambda i, e: (
                e["T1w"]["data"].get_fdata().__setitem__((0, 0, 0), 9.0)
            ),
            "T1w.data",
        ),
        (
            lambda i, e: get_data(i["mask"]).__setitem__((0, 0, 0), 9.0),
            "BOLD.mask",
        ),
        (
            lambda i, e: i["mask"].get_fdata().__setitem__((0, 0, 0), 9.0),
            "BOLD.mask",
        ),
    ],
    ids=[
        "replace",
        "add-nested",
        "remove-nested",
        "remove",
        "array-in-place",
        "image-data-in-place",
        "image-affine-in-place",
        "dataframe-in-place",
        "extra-input-cached-image-in-place",
        "not-loaded-image-nilearn-in-place",
        "not-loaded-image-nibabel-in-place",
    ],
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
        The parametrized change of the input (and extra input).
    changed : str
        The parametrized path of the changed data.

    """
    marker = _ReadingMarker(on=["BOLD"], name="changing")
    marker._change = change  # type: ignore[attr-defined]
    with pytest.raises(RuntimeError, match=rf"changing changed .*{changed}"):
        marker.fit_transform(input=_input(tmp_path))


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
        extra_input["T1w"]["data"].get_fdata()
        input["mask"].get_fdata()
        get_data(input["mask"])

    marker = _ReadingMarker(on=["BOLD"], name="reading")
    marker._change = read  # type: ignore[attr-defined]
    out = marker.fit_transform(input=_input(tmp_path))
    assert "feat" in out["BOLD"]
