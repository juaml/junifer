"""Provide tests for update meta mixin."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Union

import pytest

from junifer.pipeline.update_meta_mixin import UpdateMetaMixin


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
    dependencies: Union[set, list, str, None],
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

    class TestUpdateMetaMixin(UpdateMetaMixin):
        """Test UpdateMetaMixin."""

        _DEPENDENCIES = dependencies

    obj = TestUpdateMetaMixin()
    obj.update_meta(input, step_name=step_name)
    assert input["meta"]["step_name"]["class"] == "TestUpdateMetaMixin"
    assert input["meta"]["dependencies"] == expected
