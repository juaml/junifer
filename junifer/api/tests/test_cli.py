"""Provide tests for cli."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import List, Tuple

import pytest
from click.testing import CliRunner
from ruamel.yaml import YAML

from junifer.api.cli import _parse_elements_file, collect, run, selftest, wtf


# Configure YAML class
yaml = YAML()
yaml.default_flow_style = False
yaml.allow_unicode = True
yaml.indent(mapping=2, sequence=4, offset=2)

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
    """Test run and collect commands.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    elements : tuple of str
        The parametrized elements to operate on.

    """
    # Get test config
    infile = Path(__file__).parent / "data" / "gmd_mean.yaml"
    # Read test config
    contents = yaml.load(infile)
    # Working directory
    workdir = tmp_path / "workdir"
    contents["workdir"] = str(workdir.resolve())
    # Output directory
    outdir = tmp_path / "outdir"
    # Storage
    contents["storage"]["uri"] = str(outdir.resolve())
    # Write new test config
    outfile = tmp_path / "in.yaml"
    yaml.dump(contents, stream=outfile)
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


@pytest.mark.parametrize(
    "elements",
    [
        "sub-01",
        "sub-01\nsub-02",
        "    sub-01    ",
        "sub-01\n    sub-02",
    ],
)
def test_run_using_element_file(tmp_path: Path, elements: str) -> None:
    """Test run command using element file.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    elements : str
        The parametrized elements to write to the element file.

    """
    # Create test file
    test_file_path = tmp_path / "elements.txt"
    with open(test_file_path, "w") as f:
        f.write(elements)

    # Get test config
    infile = Path(__file__).parent / "data" / "gmd_mean.yaml"
    # Read test config
    contents = yaml.load(infile)
    # Working directory
    workdir = tmp_path / "workdir"
    contents["workdir"] = str(workdir.resolve())
    # Output directory
    outdir = tmp_path / "outdir"
    # Storage
    contents["storage"]["uri"] = str(outdir.resolve())
    # Write new test config
    outfile = tmp_path / "in.yaml"
    yaml.dump(contents, stream=outfile)
    # Run command arguments
    run_args = [
        str(outfile.absolute()),
        "--verbose",
        "debug",
        "--element",
        str(test_file_path.resolve()),
    ]
    # Invoke run command
    run_result = runner.invoke(run, run_args)
    # Check
    assert run_result.exit_code == 0


@pytest.mark.parametrize(
    "elements, expected_list",
    [
        ("sub-01,ses-01", [("sub-01", "ses-01")]),
        (
            "sub-01,ses-01\nsub-02,ses-01",
            [("sub-01", "ses-01"), ("sub-02", "ses-01")],
        ),
        ("sub-01, ses-01", [("sub-01", "ses-01")]),
        (
            "sub-01, ses-01\nsub-02, ses-01",
            [("sub-01", "ses-01"), ("sub-02", "ses-01")],
        ),
        (" sub-01 , ses-01 ", [("sub-01", "ses-01")]),
        (
            " sub-01 , ses-01 \n sub-02, ses-01 ",
            [("sub-01", "ses-01"), ("sub-02", "ses-01")],
        ),
    ],
)
def test_multi_element_access(
    tmp_path: Path, elements: str, expected_list: List[Tuple[str, ...]]
) -> None:
    """Test mulit-element parsing.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    elements : str
        The parametrized elements to write to the element file.
    expected_list : list of tuple of str
        The parametrized list of element tuples to expect.

    """
    # Create test file
    test_file_path = tmp_path / "elements_multi.txt"
    with open(test_file_path, "w") as f:
        f.write(elements)
    # Load element file
    read_elements = _parse_elements_file(test_file_path)
    # Check
    assert read_elements == expected_list


def test_wtf_short() -> None:
    """Test short version of wtf command."""
    # Invoke wtf command
    wtf_result = runner.invoke(wtf)
    # Check
    assert wtf_result.exit_code == 0


def test_wtf_long() -> None:
    """Test long version of wtf command."""
    # Invoke wtf command
    wtf_result = runner.invoke(wtf, "--long")
    # Check
    assert wtf_result.exit_code == 0


def test_selftest_invalid_arg() -> None:
    """Test selftest failure for invalid argument value."""
    # Invoke selftest command
    selftest_result = runner.invoke(selftest, "abyss")
    # Check
    assert selftest_result.exit_code == 2


def test_selftest() -> None:
    """Test selftest."""
    # Invoke selftest command
    selftest_result = runner.invoke(selftest, "tests")
    # Check; will result in 1 due to I/O descriptor manipulation
    assert selftest_result.exit_code == 1
