"""Provide functions for cli."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import pathlib
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Union

import click
import pandas as pd

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
    yaml,
)


def _parse_elements(element: Tuple[str], config: Dict) -> Union[List, None]:
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
    if len(element) == 0:
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


def _parse_elements_file(filepath: Path) -> List[Tuple[str, ...]]:
    """Parse elements from file.

    Parameters
    ----------
    filepath : pathlib.Path
        The path to the element file.

    Returns
    -------
    list of tuple of str
        The element(s) as list.

    """
    # Read CSV into dataframe
    csv_df = pd.read_csv(
        filepath,
        header=None,  # no header  # type: ignore
        index_col=False,  # no index column
        skipinitialspace=True,  # no leading space after delimiter
    )
    # Remove trailing whitespace in cell entries
    csv_df_trimmed = csv_df.apply(
        lambda x: x.str.strip() if x.dtype == "object" else x
    )
    # Convert to list of tuple of str
    return list(map(tuple, csv_df_trimmed.to_numpy().astype(str)))


def _validate_verbose(
    ctx: click.Context, param: str, value: str
) -> Union[str, int]:
    """Validate verbose option.

    Parameters
    ----------
    ctx : click.Context
        The context of the command.
    param : str
        The parameter to validate.
    value : str
        The value to validate.

    Returns
    -------
    str or int
        The validated value.
    """
    if isinstance(value, int):
        return value

    valid_strings = ["error", "warning", "info", "debug"]
    if isinstance(value, str) and value.lower() in valid_strings:
        return value.upper()

    try:
        value = int(value)  # type: ignore
        return value
    except ValueError:
        # If we get here, the value is not a valid integer.
        pass

    # If we get here, the value is not valid.
    raise click.BadParameter(
        f"verbose must be one of {valid_strings} or an integer"
    )


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
    type=click.UNPROCESSED,
    callback=_validate_verbose,
    default="info",
)
def run(
    filepath: click.Path, element: Tuple[str], verbose: Union[str, int]
) -> None:
    """Run command for CLI.

    \f

    Parameters
    ----------
    filepath : click.Path
        The filepath to the configuration file.
    element : tuple of str
        The element to operate on.
    verbose : click.Choice
        The verbosity level: warning, info or debug (default "info").

    """
    configure_logging(level=verbose)
    # TODO(synchon): add validation
    # Parse YAML
    config = parse_yaml(filepath)  # type: ignore
    # Retrieve working directory
    workdir = config["workdir"]
    # Fetch datagrabber
    datagrabber = config["datagrabber"]
    # Fetch markers
    markers = config["markers"]
    # Fetch storage
    storage = config["storage"]
    # Fetch preprocessors
    preprocessors = config.get("preprocess")
    # Convert to list if single preprocessor
    if preprocessors is not None and not isinstance(preprocessors, list):
        preprocessors = [preprocessors]
    # Parse elements
    elements = _parse_elements(element, config)
    # Perform operation
    api_run(
        workdir=workdir,
        datagrabber=datagrabber,
        markers=markers,
        storage=storage,
        preprocessors=preprocessors,
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
    type=click.UNPROCESSED,
    callback=_validate_verbose,
    default="info",
)
def collect(filepath: click.Path, verbose: Union[str, int]) -> None:
    """Collect command for CLI.

    \f

    Parameters
    ----------
    filepath : click.Path
        The filepath to the configuration file.
    verbose : click.Choice
        The verbosity level: warning, info or debug (default "info").

    """
    configure_logging(level=verbose)
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
    type=click.UNPROCESSED,
    callback=_validate_verbose,
    default="info",
)
def queue(
    filepath: click.Path,
    element: str,
    overwrite: bool,
    submit: bool,
    verbose: Union[str, int],
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
    configure_logging(level=verbose)
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
    click.echo(yaml.dump(report, stream=sys.stdout))


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


@setup.command("fsl-docker")
def fsl_docker() -> None:  # pragma: no cover
    """Configure FSL-Docker wrappers."""
    import junifer

    pkg_path = Path(junifer.__path__[0])  # type: ignore
    fsl_wrappers_path = pkg_path / "api" / "res" / "fsl"
    msg = f"""
    Installation instructions for FSL-Docker wrappers:

    1. Install Docker: https://docs.docker.com/get-docker/

    2. Get the FSL-Docker image by running this on the command line:

        docker pull brainlife/fsl

    3. Add this line to the ~/.bashrc or ~/.zshrc file:

    export PATH="$PATH:{fsl_wrappers_path}"
    """
    click.secho(msg, fg="blue")


@setup.command("ants-docker")
def ants_docker() -> None:  # pragma: no cover
    """Configure ANTs-Docker wrappers."""
    import junifer

    pkg_path = Path(junifer.__path__[0])  # type: ignore
    ants_wrappers_path = pkg_path / "api" / "res" / "ants"
    msg = f"""
    Installation instructions for ANTs-Docker wrappers:

    1. Install Docker: https://docs.docker.com/get-docker/

    2. Get the ANTs-Docker image by running this on the command line:

        docker pull antsx/ants

    3. Add this line to the ~/.bashrc or ~/.zshrc file:

    export PATH="$PATH:{ants_wrappers_path}"
    """
    click.secho(msg, fg="blue")
