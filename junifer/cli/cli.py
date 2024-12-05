"""Provide functions for CLI."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import pathlib
import subprocess
import sys
from pathlib import Path
from typing import Optional, Union

import click

from ..api import functions as cli_func
from ..utils import (
    configure_logging,
    raise_error,
    yaml,
)
from .parser import parse_elements, parse_yaml
from .utils import (
    _get_dependency_information,
    _get_environment_information,
    _get_junifer_version,
    _get_python_information,
    _get_system_information,
)


__all__ = [
    "afni_docker",
    "ants_docker",
    "cli",
    "collect",
    "freesurfer_docker",
    "fsl_docker",
    "list_elements",
    "queue",
    "reset",
    "run",
    "selftest",
    "setup",
    "wtf",
]


def _validate_optional_verbose(
    ctx: click.Context, param: str, value: Optional[str]
):
    """Validate optional verbose option.

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
    str or int or None
        The validated value.

    """
    if value is None:
        return value
    else:
        return _validate_verbose(ctx, param, value)


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
    """JUelich NeuroImaging FEature extractoR."""


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
@click.option(
    "--verbose-datalad",
    type=click.UNPROCESSED,
    callback=_validate_optional_verbose,
    default=None,
)
def run(
    filepath: click.Path,
    element: tuple[str],
    verbose: Union[str, int],
    verbose_datalad: Optional[Union[str, int]],
) -> None:
    """Run feature extraction.

    \f

    Parameters
    ----------
    filepath : click.Path
        The filepath to the configuration file.
    element : tuple of str
        The element(s) to operate on.
    verbose : click.Choice
        The verbosity level: warning, info or debug (default "info").
    verbose_datalad : click.Choice or None
        The verbosity level for datalad: warning, info or debug (default None).

    """
    # Setup logging
    configure_logging(level=verbose, level_datalad=verbose_datalad)
    # TODO(synchon): add validation
    # Parse YAML
    config = parse_yaml(filepath)
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
    elements = parse_elements(element, config)
    # Perform operation
    cli_func.run(
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
@click.option(
    "--verbose-datalad",
    type=click.UNPROCESSED,
    callback=_validate_optional_verbose,
    default=None,
)
def collect(
    filepath: click.Path,
    verbose: Union[str, int],
    verbose_datalad: Union[str, int, None],
) -> None:
    """Collect extracted features.

    \f

    Parameters
    ----------
    filepath : click.Path
        The filepath to the configuration file.
    verbose : click.Choice
        The verbosity level: warning, info or debug (default "info").
    verbose_datalad : click.Choice or None
        The verbosity level for datalad: warning, info or debug (default None).

    """
    # Setup logging
    configure_logging(level=verbose, level_datalad=verbose_datalad)
    # TODO: add validation
    # Parse YAML
    config = parse_yaml(filepath)
    # Fetch storage
    storage = config["storage"]
    # Perform operation
    cli_func.collect(storage=storage)


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
@click.option(
    "--verbose-datalad",
    type=click.UNPROCESSED,
    callback=_validate_optional_verbose,
    default=None,
)
def queue(
    filepath: click.Path,
    element: tuple[str],
    overwrite: bool,
    submit: bool,
    verbose: Union[str, int],
    verbose_datalad: Union[str, int, None],
) -> None:
    """Queue feature extraction.

    \f

    Parameters
    ----------
    filepath : click.Path
        The filepath to the configuration file.
    element : tuple of str
        The element(s) to operate on.
    overwrite : bool
        Whether to overwrite existing directory.
    submit : bool
        Whether to submit the job.
    verbose : click.Choice
        The verbosity level: warning, info or debug (default "info").
    verbose_datalad : click.Choice or None
        The verbosity level for datalad: warning, info or debug (default None).

    Raises
    ------
    ValueError
        If no ``queue`` section is found in the YAML.

    """
    # Setup logging
    configure_logging(level=verbose, level_datalad=verbose_datalad)
    # TODO: add validation
    # Parse YAML
    config = parse_yaml(filepath)  # type: ignore
    # Check queue section
    if "queue" not in config:
        raise_error(f"No queue configuration found in {filepath}.")
    # Parse elements
    elements = parse_elements(element, config)
    # Separate out queue section
    queue_config = config.pop("queue")
    kind = queue_config.pop("kind")
    # Perform operation
    cli_func.queue(
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
    """WTF?!.

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
    """Selftest.

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
@click.option(
    "--verbose-datalad",
    type=click.UNPROCESSED,
    callback=_validate_optional_verbose,
    default=None,
)
def reset(
    filepath: click.Path,
    verbose: Union[str, int],
    verbose_datalad: Union[str, int, None],
) -> None:
    """Reset generated assets.

    \f

    Parameters
    ----------
    filepath : click.Path
        The filepath to the configuration file.
    verbose : click.Choice
        The verbosity level: warning, info or debug (default "info").
    verbose_datalad : click.Choice or None
        The verbosity level for datalad: warning, info or debug (default None).

    """
    # Setup logging
    configure_logging(level=verbose, level_datalad=verbose_datalad)
    # Parse YAML
    config = parse_yaml(filepath)
    # Perform operation
    cli_func.reset(config)


@cli.command()
@click.argument(
    "filepath",
    type=click.Path(
        exists=True, readable=True, dir_okay=False, path_type=pathlib.Path
    ),
)
@click.option("--element", type=str, multiple=True)
@click.option(
    "-o",
    "--output-file",
    type=click.Path(dir_okay=False, writable=True, path_type=pathlib.Path),
)
@click.option(
    "-v",
    "--verbose",
    type=click.UNPROCESSED,
    callback=_validate_verbose,
    default="info",
)
@click.option(
    "--verbose-datalad",
    type=click.UNPROCESSED,
    callback=_validate_optional_verbose,
    default=None,
)
def list_elements(
    filepath: click.Path,
    element: tuple[str],
    output_file: Optional[click.Path],
    verbose: Union[str, int],
    verbose_datalad: Union[str, int, None],
) -> None:
    """List elements of a dataset.

    \f

    Parameters
    ----------
    filepath : click.Path
        The filepath to the configuration file.
    element : tuple of str
        The element(s) to operate on.
    output_file : click.Path or None
        The path to write the output to. If not None, writing to
        stdout is not performed.
    verbose : click.Choice
        The verbosity level: warning, info or debug (default "info").
    verbose_datalad : click.Choice or None
        The verbosity level for datalad: warning, info or debug (default None

    """
    # Setup logging
    configure_logging(level=verbose, level_datalad=verbose_datalad)
    # Parse YAML
    config = parse_yaml(filepath)
    # Fetch datagrabber
    datagrabber = config["datagrabber"]
    # Parse elements
    elements = parse_elements(element, config)
    # Perform operation
    listed_elements = cli_func.list_elements(
        datagrabber=datagrabber,
        elements=elements,
    )
    # Check if output file is provided
    if output_file is not None:
        output_file.touch()
        output_file.write_text(listed_elements)
    else:
        click.secho(listed_elements, fg="blue")


@cli.group()
def setup() -> None:  # pragma: no cover
    """Configure external tools."""
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


@setup.command("freesurfer-docker")
def freesurfer_docker() -> None:  # pragma: no cover
    """Configure FreeSurfer-Docker wrappers."""
    import junifer

    pkg_path = Path(junifer.__path__[0])  # type: ignore
    fs_wrappers_path = pkg_path / "api" / "res" / "freesurfer"
    msg = f"""
    Installation instructions for FreeSurfer-Docker wrappers:

    1. Install Docker: https://docs.docker.com/get-docker/

    2. Get the FreeSurfer-Docker image by running this on the command line:

        docker pull freesurfer/freesurfer

    3. Get license from: https://surfer.nmr.mgh.harvard.edu/registration.html .
       You can skip this step if you already have one.

    4. Add this line to the ~/.bashrc or ~/.zshrc file:

    export PATH="$PATH:{fs_wrappers_path}"
    """
    click.secho(msg, fg="blue")
