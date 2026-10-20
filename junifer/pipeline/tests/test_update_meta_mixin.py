"""Provide tests for update meta mixin."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import pytest
from pydantic import BaseModel

from junifer.pipeline import UpdateMetaMixin


@pytest.mark.parametrize(
    "input, step_name, dependencies, expected",
    [
        ({}, "step_name", None, set()),
        ({}, "step_name", ["numpy"], {"numpy"}),
        ({}, "step_name", "numpy", {"numpy"}),
        ({}, "step_name", {"numpy"}, {"numpy"}),
    ],
)
def test_UpdateMetaMixin(
    input: dict,
    step_name: str,
    dependencies: set | list | str | None,
    expected: set,
) -> None:
    """Test UpdateMetaMixin.

    Parameters
    ----------
    input : dict
        The data object to update.
    step_name : str
        The name of the pipeline step.
    dependencies : set, list, None, str
        The dependencies of the pipeline step.
    expected : set
        The expected dependencies.

    """

    class TestUpdateMetaMixin(BaseModel, UpdateMetaMixin):
        """Test UpdateMetaMixin."""

        _DEPENDENCIES = dependencies

    obj = TestUpdateMetaMixin()
    obj.update_meta(input, step_name=step_name)
    assert input["meta"]["step_name"]["class"] == "TestUpdateMetaMixin"
    assert input["meta"]["dependencies"] == expected


def test_UpdateMetaMixin_fields_set() -> None:
    """Test the parameters set when creating the object are stored.

    They are the parameters passed, not the ones set when validating them
    (e.g., the name and data types of a marker).

    """
    from junifer.markers import ParcelAggregation

    marker = ParcelAggregation(parcellation="Schaefer100x7", method="mean")
    data = {}
    marker.update_meta(data, step_name="marker")
    meta = data["meta"]["marker"]
    assert meta["_fields_set"] == ["method", "parcellation"]
    # Set when validating, but not stored as set
    assert meta["name"] == "ParcelAggregation"
    assert meta["on"] is not None
    # Built-in, so no module to load it
    assert "_with" not in meta


def test_UpdateMetaMixin_with() -> None:
    """Test the module registering a component is stored."""
    from junifer.api.decorators import register_marker
    from junifer.markers import ParcelAggregation
    from junifer.pipeline import PipelineComponentRegistry

    @register_marker
    class MyParcelAggregation(ParcelAggregation):
        """Parcel aggregation registered in the test."""

    try:
        marker = MyParcelAggregation(parcellation="Schaefer100x7")
        data = {}
        marker.update_meta(data, step_name="marker")
        assert data["meta"]["marker"]["_with"] == __name__
    finally:
        PipelineComponentRegistry().deregister(
            step="marker", klass=MyParcelAggregation
        )


def test_UpdateMetaMixin_fields_set_post_init(tmp_path) -> None:
    """Test the parameters set with subclasses overriding model_post_init.

    The parameters set are stored even if ``model_post_init`` does not call
    the one of the base class, or changes parameters before calling it.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    from typing import Any

    from junifer.datagrabber import PatternDataGrabber
    from junifer.markers import ParcelAggregation

    class MyMarker(ParcelAggregation):
        """Marker not calling the model_post_init of its base class."""

        def model_post_init(self, context: Any) -> None:
            self.method = "std"

    class MyDataGrabber(PatternDataGrabber):
        """DataGrabber changing a parameter before validating."""

        check_files: bool = False

        def model_post_init(self, context: Any) -> None:
            self.check_files = True
            super().model_post_init(context)

    marker = MyMarker(parcellation="Schaefer100x7")
    datagrabber = MyDataGrabber(
        types=["BOLD"],
        patterns={"BOLD": {"pattern": "{subject}.nii", "space": "native"}},
        replacements=["subject"],
        datadir=tmp_path,
    )
    for obj, expected in (
        (marker, ["parcellation"]),
        (datagrabber, ["datadir", "patterns", "replacements", "types"]),
    ):
        data = {}
        obj.update_meta(data, step_name="step")
        assert data["meta"]["step"]["_fields_set"] == expected
