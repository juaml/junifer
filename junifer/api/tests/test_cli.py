"""Provide tests for cli."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import Tuple

import pytest
import yaml
from click.testing import CliRunner

from junifer.api.cli import collect, run


# Create click test runner
runner = CliRunner()


# TODO: adapt elements to take arrays
@pytest.mark.parametrize(
    "elements",
    [
        ("sub-01", "sub-02", "sub-03"),
        ("sub-01", "sub-02", "sub-04"),
    ],
)
def test_run_and_collect_commands(
    tmp_path: Path, elements: Tuple[str, ...]
) -> None:
    """Test run and collect commands."""
    # Get test config
    infile = Path(__file__).parent / "data" / "gmd_mean.yaml"
    # Read test config
    with open(infile, mode="r") as f:
        contents = yaml.safe_load(f)
    # Working directory
    workdir = tmp_path / "workdir"
    contents["workdir"] = str(workdir.absolute())
    # Output directory
    outdir = tmp_path / "outdir"
    # Storage
    contents["storage"]["uri"] = str(outdir.absolute())
    # Write new test config
    outfile = tmp_path / "in.yaml"
    with open(outfile, mode="w") as f:
        yaml.dump(contents, f)
    # Run command arguments
    run_args = [
        str(outfile.absolute()),
        "--verbose",
        "debug",
        "--element",
        elements[0],
        "--element",
        elements[1],
        "--element",
        elements[2],
    ]
    # Invoke run command
    run_result = runner.invoke(run, run_args)
    # Check
    assert run_result.exit_code == 0
    # Collect command arguments
    collect_args = [str(outfile.absolute()), "--verbose", "debug"]
    # Invoke collect command
    collect_result = runner.invoke(collect, collect_args)
    # Check
    assert collect_result.exit_code == 0
