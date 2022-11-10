"""Testing utils."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from pathlib import Path


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
