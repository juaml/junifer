"""Provide conftest for pytest."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import gc

import pytest

from junifer.utils.singleton import Singleton


# Do not collect the tests of vendored packages. Paths are relative to this
# file, so it also works when testing the installed package.
collect_ignore = ["external/h5io", "external/BrainPrint"]


def pytest_collection_finish(session: pytest.Session) -> None:
    """Exclude the objects alive after collection from garbage collection.

    nilearn (< 0.14) forces a full garbage collection every time it gets
    the data of an image, which has to go over all the objects of the test
    session (modules, collected tests, etc.). Freezing them makes these
    collections much faster.

    Parameters
    ----------
    session : pytest.Session
        The pytest session.

    """
    gc.collect()
    gc.freeze()


@pytest.fixture(autouse=True)
def reset_singletons() -> None:
    """Reset all singletons."""
    to_clean = ["WorkDirManager"]
    to_remove = [
        v for k, v in Singleton.instances.items() if k.__name__ in to_clean
    ]
    Singleton.instances = {
        k: v
        for k, v in Singleton.instances.items()
        if k.__name__ not in to_clean
    }
    # Force deleting the singletons
    for elem in to_remove:
        del elem


@pytest.fixture(autouse=True)
def clear_computation_caches() -> None:
    """Clear the cached computations of ReHo and ALFF estimators.

    The estimators are singletons whose ``compute`` is cached per input
    path, so results from earlier tests would otherwise be reused.

    """
    from junifer.markers.falff._afni_falff import AFNIALFF
    from junifer.markers.falff._junifer_falff import JuniferALFF
    from junifer.markers.reho._afni_reho import AFNIReHo
    from junifer.markers.reho._junifer_reho import JuniferReHo

    for klass in (AFNIALFF, JuniferALFF, AFNIReHo, JuniferReHo):
        klass.compute.cache_clear()
