"""Provide functions for parser."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import importlib
import importlib.util
import os
import sys
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
    if "elements" in contents:
        if contents["elements"] is None:
            raise_error(
                "The elements key was defined but its content is empty. "
                "Please define the elements to operate on or remove the key."
            )
    # load modules
    if "with" in contents:
        to_load = contents["with"]
        # Convert load modules to list
        if not isinstance(to_load, list):
            to_load = [to_load]
        for t_module in to_load:
            if t_module.endswith(".py"):
                logger.debug(f"Importing file: {t_module}")
                file_path = Path(os.getcwd()) / t_module
                if not file_path.exists():
                    raise_error(
                        f"File in 'with' section does not exist: {file_path}"
                    )
                spec = importlib.util.spec_from_file_location(
                    t_module, file_path
                )
                module = importlib.util.module_from_spec(spec)  # type: ignore
                sys.modules[t_module] = module
                spec.loader.exec_module(module)  # type: ignore
            else:
                logger.info(f"Importing module: {t_module}")
                importlib.import_module(t_module)

    return contents
