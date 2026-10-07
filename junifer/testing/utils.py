"""Testing utils."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from ..utils import config
from ..utils._config import ConfigVal


__all__ = ["config_override", "get_testing_data"]


def get_testing_data(fname: str) -> Path:
    """Get the path to a testing data file.

    Parameters
    ----------
    fname : str
        The name of the file.

    Returns
    -------
    pathlib.Path
        The absolute path to the file.

    """
    t_path = Path(__file__).parent / "data" / fname
    if not t_path.exists():
        raise FileNotFoundError(f"File {fname} not found in testing data")
    return t_path.resolve()


@contextmanager
def config_override(key: str, val: ConfigVal) -> Iterator[None]:
    """Temporarily set a configuration parameter.

    The previous state is restored on exit: the previous value if the key
    was set, otherwise the key is deleted.

    Parameters
    ----------
    key : str
        The configuration key to set.
    val : bool or int or float
        The value to set ``key`` to.

    """
    missing = object()
    prev = config.get(key, missing)
    config.set(key, val)
    try:
        yield
    finally:
        if prev is missing:
            config.delete(key)
        else:
            config.set(key, prev)
