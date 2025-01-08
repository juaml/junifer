"""Provide functions for CLI parser."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Union

import pandas as pd

from ..typing import Elements
from ..utils import logger, raise_error, warn_with_log, yaml


__all__ = ["parse_elements", "parse_yaml"]


def parse_yaml(filepath: Union[str, Path]) -> dict:  # noqa: C901
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
                # Add the parent directory to the sys.path so that the
                # any imports from this module work correctly
                t_path = str(file_path.parent)
                if t_path not in sys.path:
                    sys.path.append(str(file_path.parent))

                spec = importlib.util.spec_from_file_location(
                    t_module, file_path
                )
                module = importlib.util.module_from_spec(spec)  # type: ignore
                sys.modules[t_module] = module
                spec.loader.exec_module(module)  # type: ignore

                # Add absolute path to final list
                final_to_load.append(str(file_path.resolve()))

                # Check if the module has junifer_module_deps function
                if hasattr(module, "junifer_module_deps"):
                    logger.debug(
                        f"Module {t_module} has junifer_module_deps function"
                    )
                    # Get the dependencies
                    deps = module.junifer_module_deps()
                    # Add the dependencies to the final list
                    for dep in deps:
                        if dep not in final_to_load:
                            final_to_load.append(
                                str((file_path.parent / dep).resolve())
                            )
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


def parse_elements(
    element: tuple[str, ...], config: dict
) -> Union[Elements, None]:
    """Parse elements from cli.

    Parameters
    ----------
    element : tuple of str
        The element(s) to operate on.
    config : dict
        The configuration to operate using.

    Returns
    -------
    list or None
        The element(s) as list or None.

    Raises
    ------
    ValueError
        If no element is found either in the command-line options or
        the configuration file.

    Warns
    -----
    RuntimeWarning
        If elements are specified both via the command-line options and
        the configuration file.

    """
    logger.debug(f"Parsing elements: {element}")
    # Early return None to continue with all elements
    if not element:
        return None
    # Check if the element is a file for single element;
    # if yes, then parse elements from it
    if len(element) == 1 and Path(element[0]).resolve().is_file():
        elements = _parse_elements_file(Path(element[0]).resolve())
    else:
        # Process multi-keyed elements
        elements = [tuple(x.split(",")) if "," in x else x for x in element]
    logger.debug(f"Parsed elements: {elements}")
    if elements is not None and "elements" in config:
        warn_with_log(
            "One or more elements have been specified in both the command "
            "line and in the config file. The command line has precedence "
            "over the configuration file. That is, the elements specified "
            "in the command line will be used. The elements specified in "
            "the configuration file will be ignored. To remove this warning, "
            "please remove the `elements` item from the configuration file."
        )
    elif elements is None:
        # Check in config
        elements = config.get("elements", None)
        if elements is None:
            raise_error(
                "The `elements` key is set in the configuration, but its value"
                " is `None`. It is likely that there is an empty `elements` "
                "section in the yaml configuration file."
            )
    return elements


def _parse_elements_file(filepath: Path) -> Elements:
    """Parse elements from file.

    Parameters
    ----------
    filepath : pathlib.Path
        The path to the element file.

    Returns
    -------
    list
        The element(s) as list.

    """
    # Read CSV into dataframe
    csv_df = pd.read_csv(
        filepath,
        header=None,  # no header  # type: ignore
        index_col=False,  # no index column
        dtype=str,
        skipinitialspace=True,  # no leading space after delimiter
    )
    # Remove trailing whitespace in cell entries
    csv_df_trimmed = csv_df.apply(lambda x: x.str.strip())
    # Convert to list of tuple of str if more than one column else flatten
    if len(csv_df_trimmed.columns) == 1:
        return csv_df_trimmed.to_numpy().flatten().tolist()
    else:
        return list(map(tuple, csv_df_trimmed.to_numpy()))
