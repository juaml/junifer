"""Provide functions for parser."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import importlib
from pathlib import Path
from typing import Dict, Union

import yaml

from ..utils.logging import logger, raise_error


def parse_yaml(filepath: Union[str, Path]) -> Dict:
    """Parse YAML.

    Parameters
    ----------
    filepath : str or pathlib.Path
        The filepath to read from.

    Returns
    -------
    dict
        The contents represented as dictionary.

    """
    # Convert str to Path
    if not isinstance(filepath, Path):
        filepath = Path(filepath)

    logger.info(f"Parsing yaml file: {str(filepath.absolute())}")
    # Filepath existence check
    if not filepath.exists():
        raise_error(f"File does not exist: {str(filepath.absolute())}")
    # Filepath reading
    with open(filepath, "r") as f:
        contents = yaml.safe_load(f)
    # Autload modules
    if "with" in contents:
        to_load = contents["with"]
        # Convert autload modules to list
        if not isinstance(to_load, list):
            to_load = [to_load]
        for t_module in to_load:
            logger.info(f"Importing module: {t_module}")
            importlib.import_module(t_module)

    return contents
