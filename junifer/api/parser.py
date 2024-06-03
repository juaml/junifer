"""Provide functions for parser."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Dict, Union

from ..utils.logging import logger, raise_error
from .utils import yaml


__all__ = ["parse_yaml"]


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

    logger.info(f"Parsing yaml file: {filepath.absolute()!s}")
    # Filepath existence check
    if not filepath.exists():
        raise_error(f"File does not exist: {filepath.absolute()!s}")
    # Filepath reading
    contents = yaml.load(filepath)
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
        # Initialize list to have absolute paths for custom modules
        final_to_load = []
        for t_module in to_load:
            if t_module.endswith(".py"):
                logger.debug(f"Importing file: {t_module}")
                # This resolves both absolute and relative paths
                file_path = filepath.parent / t_module
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
                # Add absolute path to final list
                final_to_load.append(str(file_path.resolve()))
            else:
                logger.info(f"Importing module: {t_module}")
                importlib.import_module(t_module)
                # Add module to final list
                final_to_load.append(t_module)

        # Replace modules to be loaded so that custom modules will take the
        # absolute path. This was not the case as found in #224. Similar thing
        # is done with the storage URI below.
        contents["with"] = final_to_load

    # Compute path for the URI parameter in storage files that are relative
    # This is a tricky thing that appeared in #127. The problem is that
    # the path in the URI parameter is relative to YAML file, not to the
    # current working directory. If we leave it as is in the contents
    # dict, then it will be used later in the ``build`` function as is,
    # which will be computed relative to the current working directory.
    # The solution is to compute the absolute path and replace the
    # relative path in the contents dict with the absolute path.

    # Check if the storage file is defined
    if "storage" in contents:
        if "uri" in contents["storage"]:
            # Check if the storage file is relative
            uri_path = Path(contents["storage"]["uri"])
            if not uri_path.is_absolute():
                # Compute the absolute path
                contents["storage"]["uri"] = str(
                    (filepath.parent / uri_path).resolve()
                )

    # Allow relative path if queue env kind is venv; same motivation as above
    if "queue" in contents:
        if "env" in contents["queue"]:
            if "venv" == contents["queue"]["env"]["kind"]:
                # Check if the env name is relative
                venv_path = Path(contents["queue"]["env"]["name"])
                if not venv_path.is_absolute():
                    # Compute the absolute path
                    contents["queue"]["env"]["name"] = str(
                        (filepath.parent / venv_path).resolve()
                    )

    return contents
