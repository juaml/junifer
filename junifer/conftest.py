"""Provide conftest for pytest."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
import pytest

from junifer.utils.singleton import Singleton


@pytest.fixture(autouse=True)
def reset_singletons() -> None:
    """Reset all singletons."""
    to_clean = ["WorkDirManager"]
    Singleton.instances = {
        k: v
        for k, v in Singleton.instances.items()
        if k.__name__ not in to_clean
    }
