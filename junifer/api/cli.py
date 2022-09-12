"""Provide functions for cli."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import pathlib
from typing import Dict, List, Union

import click

from ..utils.logging import configure_logging, logger, warn_with_log
from .functions import collect as api_collect
from .functions import queue as api_queue
from .functions import run as api_run
from .parser import parse_yaml


def _parse_elements(element: str, config: Dict) -> Union[List, None]:
    """Parse elements from cli.

    Parameters
    ----------
    element : str
        The element to operate on.
    config : dict
        The configuration to operate using.

    Returns
    -------
    list
        The element(s) as list.

    """
    logger.debug(f"Parsing elements: {element}")
    if len(element) == 0:
        return None
    # TODO: If len == 1, check if its a file, then parse elements from file
    elements = [x.split(",") if "," in x else x for x in element]
    logger.debug(f"Parsed elements: {elements}")
    if elements is not None and "elements" in config:
        warn_with_log(
            "One or more elements have been specified in both the command "
            "line and in the config file. The command line has precedence "
            "over the configuration file. That is, the elements specified "
            "in the command line will be used. The elements specified in "
            "the configuration file will be ignored. To remove this warning, "
            'please remove the "elements" item from the configuration file.'
        )
    elif elements is None:
        elements = config.get("elements", None)
    return elements


@click.group()
def cli() -> None:  # pragma: no cover
    """CLI for JUelich NeuroImaging FEature extractoR."""


@cli.command()
@click.argument(
    "filepath",
    type=click.Path(
        exists=True, readable=True, dir_okay=False, path_type=pathlib.Path
    ),
)
@click.option("--element", type=str, multiple=True)
@click.option(
    "-v",
    "--verbose",
    type=click.Choice(["warning", "info", "debug"], case_sensitive=False),
    default="info",
)
def run(filepath: click.Path, element: str, verbose: click.Choice) -> None:
    """Run command for CLI.

    Parameters
    ----------
    filepath : click.Path
        The filepath to the configuration file.
    element : str
        The element to operate using.
    verbose : click.Choice
        The verbosity level: warning, info or debug (default "info").

    """
    configure_logging(level=str(verbose).upper())
    # TODO: add validation
    config = parse_yaml(filepath)  # type: ignore
    workdir = config["workdir"]
    datagrabber = config["datagrabber"]
    markers = config["markers"]
    storage = config["storage"]
    elements = _parse_elements(element, config)
    # Perform operation
    api_run(
        workdir=workdir,
        datagrabber=datagrabber,
        markers=markers,
        storage=storage,
        elements=elements,
    )


@cli.command()
@click.argument(
    "filepath",
    type=click.Path(
        exists=True, readable=True, dir_okay=False, path_type=pathlib.Path
    ),
)
@click.option(
    "-v",
    "--verbose",
    type=click.Choice(["warning", "info", "debug"], case_sensitive=False),
    default="info",
)
def collect(filepath: click.Path, verbose: click.Choice) -> None:
    """Collect command for CLI.

    Parameters
    ----------
    filepath : click.Path
        The filepath to the configuration file.
    verbose : click.Choice
        The verbosity level: warning, info or debug (default "info").

    """
    configure_logging(level=str(verbose).upper())
    # TODO: add validation
    config = parse_yaml(filepath)  # type: ignore
    storage = config["storage"]
    # Perform operation
    api_collect(storage=storage)


@cli.command()
@click.argument(
    "filepath",
    type=click.Path(
        exists=True, readable=True, dir_okay=False, path_type=pathlib.Path
    ),
)
@click.option("--element", type=str, multiple=True)
@click.option("--overwrite", is_flag=True)
@click.option("--submit", is_flag=True)
@click.option(
    "-v",
    "--verbose",
    type=click.Choice(["warning", "info", "debug"], case_sensitive=False),
    default="info",
)
def queue(
    filepath: click.Path,
    element: str,
    overwrite: bool,
    submit: bool,
    verbose: click.Choice,
) -> None:
    """Queue command for CLI.

    Parameters
    ----------
    filepath : click.Path
        The filepath to the configuration file.
    element : str
        The element to operate using.
    overwrite : bool
        Whether to overwrite existing directory.
    submit : bool
        Whether to submit the job.
    verbose : click.Choice
        The verbosity level: warning, info or debug (default "info").

    """
    configure_logging(level=str(verbose).upper())
    # TODO: add validation
    config = parse_yaml(filepath)  # type: ignore
    elements = _parse_elements(element, config)
    queue_config = config.pop("queue")
    kind = queue_config.pop("kind")
    api_queue(
        config=config,
        kind=kind,
        overwrite=overwrite,
        elements=elements,
        submit=submit,
        **queue_config,
    )


@cli.command()
def selftest() -> None:
    """Selftest command for CLI."""
    pass
