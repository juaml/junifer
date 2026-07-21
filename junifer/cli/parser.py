"""Provide functions for CLI parser."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

import pandas as pd

from ..typing import Elements
from ..utils import logger, raise_error, warn_with_log


__all__ = ["parse_elements"]


def parse_elements(element: tuple[str, ...], config: dict) -> Elements | None:
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
