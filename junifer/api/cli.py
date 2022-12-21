"""Provide functions for cli."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import pathlib
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Union

import click
import yaml

from ..utils.logging import (
    configure_logging,
    logger,
    raise_error,
    warn_with_log,
)
from .functions import collect as api_collect
from .functions import queue as api_queue
from .functions import run as api_run
from .parser import parse_yaml
from .utils import (
    _get_dependency_information,
    _get_environment_information,
    _get_junifer_version,
    _get_python_information,
    _get_system_information,
)


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
    elements = [tuple(x.split(",")) if "," in x else x for x in element]
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
        if elements is None:
            raise_error(
                "The 'elements' key is set in the configuration, but its value"
                " is 'None'. It is likely that there is an empty 'elements' "
                "section in the yaml configuration file."
            )
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
    \f
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
    preprocessor = config.get("preprocess")
    elements = _parse_elements(element, config)
    # Perform operation
    api_run(
        workdir=workdir,
        datagrabber=datagrabber,
        markers=markers,
        storage=storage,
        preprocessor=preprocessor,
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
    \f
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
    \f
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
    if "queue" not in config:
        raise_error(f"No queue configuration found in {filepath}.")
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
@click.option("--long", "long_", is_flag=True)
def wtf(long_: bool) -> None:
    """Wtf command for CLI.
    \f
    Parameters
    ----------
    long_ : bool
        Whether to report long version or not.

    """
    report = {
        "junifer": _get_junifer_version(),
        "python": _get_python_information(),
        "dependencies": _get_dependency_information(long_=long_),
        "system": _get_system_information(),
        "environment": _get_environment_information(long_=long_),
    }
    click.echo(yaml.dump(report, sort_keys=False))


@cli.command()
@click.argument("subpkg", type=str)
def selftest(subpkg: str) -> None:
    """Selftest command for CLI.
    \f
    Parameters
    ----------
    subpkg : {"all", "api", "configs", "data", "datagrabber", "datareader",
        "markers", "pipeline", "preprocess", "storage", "testing", "utils",
        "stats"}
        The sub-package to run tests for.

    Raises
    ------
    click.BadArgumentUsage
        If `subpkg` is invalid.

    """
    sub_packages = [
        "all",
        "api",
        "configs",
        "data",
        "datagrabber",
        "datareader",
        "markers",
        "pipeline",
        "preprocess",
        "storage",
        "testing",
        "tests",
        "utils",
    ]
    if subpkg not in sub_packages:
        raise click.BadArgumentUsage(
            f"Invalid value for argument `subpkg`: {subpkg}. "
            f"Should be one of {sub_packages}"
        )

    if subpkg == "all":
        completed_process = subprocess.run(
            ["pytest", "-vvv"],
            stdin=subprocess.DEVNULL,
            stdout=sys.stdout,
            stderr=subprocess.STDOUT,
            cwd=Path(__file__).parent.parent.parent.absolute(),
            check=False,
        )
    else:
        completed_process = subprocess.run(
            ["pytest", f"junifer/{subpkg}", "-vvv"],
            stdin=subprocess.DEVNULL,
            stdout=sys.stdout,
            stderr=subprocess.STDOUT,
            cwd=Path(__file__).parent.parent.parent.absolute(),
            check=False,
        )

    if completed_process.returncode == 0:
        click.secho("Successful.", fg="green")
    else:
        click.secho("Failure.", fg="red")


@cli.group()
def setup() -> None:  # pragma: no cover
    """Configure commands for Junifer."""
    pass


@setup.command("afni-docker")
def afni_docker() -> None:  # pragma: no cover
    """Configure AFNI-Docker wrappers."""
    import junifer

    pkg_path = Path(junifer.__path__[0])  # type: ignore
    afni_wrappers_path = pkg_path / "api" / "res" / "afni"
    msg = f"""
    Installation instructions for AFNI-Docker wrappers:

    1. Install Docker: https://docs.docker.com/get-docker/

    2. Get the AFNI-Docker image by running this on the command line:

        docker pull afni/afni

    3. Add this line to the ~/.bashrc or ~/.zshrc file:

    export PATH="$PATH:{afni_wrappers_path}"
    """
    click.secho(msg, fg="blue")
