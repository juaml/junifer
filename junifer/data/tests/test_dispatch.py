"""Provide tests for data dispatching."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import pytest

from junifer.data import (
    BasePipelineDataRegistry,
    deregister_data,
    get_data,
    list_data,
    load_data,
    register_data,
)
from junifer.data._dispatch import DataDispatcher


def test_dispatcher_addition_errors() -> None:
    """Test registry addition errors."""
    with pytest.raises(ValueError, match="Cannot set"):
        DataDispatcher()["mask"] = dict

    with pytest.raises(ValueError, match="Invalid"):
        DataDispatcher()["masks"] = dict


def test_dispatcher_removal_errors() -> None:
    """Test registry removal errors."""
    with pytest.raises(ValueError, match="Cannot delete"):
        _ = DataDispatcher().pop("mask")

    with pytest.raises(KeyError, match="masks"):
        del DataDispatcher()["masks"]


def test_dispatcher() -> None:
    """Test registry addition and removal."""

    class DumDum(BasePipelineDataRegistry):
        def register():
            pass

        def deregister():
            pass

        def load():
            pass

        def get():
            pass

    DataDispatcher().update({"masks": DumDum})
    assert "masks" in DataDispatcher()

    _ = DataDispatcher().pop("masks")
    assert "masks" not in DataDispatcher()


def test_get_data_error() -> None:
    """Test error for get_data()."""
    with pytest.raises(ValueError, match="Unknown data kind"):
        get_data(kind="planet", names="neptune", target_data={})


def test_list_data_error() -> None:
    """Test error for list_data()."""
    with pytest.raises(ValueError, match="Unknown data kind"):
        list_data(kind="planet")


def test_load_data_error() -> None:
    """Test error for load_data()."""
    with pytest.raises(ValueError, match="Unknown data kind"):
        load_data(kind="planet", name="neptune")


def test_register_data_error() -> None:
    """Test error for register_data()."""
    with pytest.raises(ValueError, match="Unknown data kind"):
        register_data(kind="planet", name="neptune", space="milkyway")


def test_deregister_data_error() -> None:
    """Test error for deregister_data()."""
    with pytest.raises(ValueError, match="Unknown data kind"):
        deregister_data(kind="planet", name="neptune")
