"""Provide tests for public decorators."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from junifer.api.decorators import register_data_registry
from junifer.data import BasePipelineDataRegistry, DataDispatcher


def test_register_data_registry() -> None:
    """Test data registry registration."""

    @register_data_registry("dumb")
    class DumDum(BasePipelineDataRegistry):
        def __init__(self):
            super().__init__()

        def register(self):
            pass

        def deregister(self):
            pass

        def load(self):
            pass

        def get(self):
            pass

    assert "dumb" in DataDispatcher()
    _ = DataDispatcher().pop("dumb")
    assert "dumb" not in DataDispatcher()
