"""Provide tests for CLI."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import Callable

import pytest
from click.testing import CliRunner
from ruamel.yaml import YAML

from junifer.cli.cli import (
    collect,
    list_elements,
    queue,
    reset,
    run,
    selftest,
    wtf,
)
from junifer.cli.parser import _parse_elements_file


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
    tmp_path: Path, elements: tuple[str, ...]
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
    infile = Path(__file__).parent / "data" / "partly_cloudy_agg_mean_tian.yml"
    # Read test config
    contents = yaml.load(infile)
    # Working directory
    contents["workdir"] = str(tmp_path.resolve())
    # Storage
    contents["storage"]["uri"] = str((tmp_path / "out.hdf5").resolve())
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
    infile = Path(__file__).parent / "data" / "partly_cloudy_agg_mean_tian.yml"
    # Read test config
    contents = yaml.load(infile)
    # Working directory
    contents["workdir"] = str(tmp_path.resolve())
    # Storage
    contents["storage"]["uri"] = str((tmp_path / "out.hdf5").resolve())
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
        ("001,01", [("001", "01")]),
        (
            "001,01\n002,02",
            [("001", "01"), ("002", "02")],
        ),
        ("001, 01", [("001", "01")]),
        (
            "001, 01\n002, 02",
            [("001", "01"), ("002", "02")],
        ),
        (" 001 , 01 ", [("001", "01")]),
        (
            " 001 , 01 \n 002, 02 ",
            [("001", "01"), ("002", "02")],
        ),
    ],
)
def test_multi_element_access(
    tmp_path: Path, elements: str, expected_list: list[tuple[str, ...]]
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


def test_queue(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test queue command.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    monkeypatch : pytest.MonkeyPatch
        The pytest.MonkeyPatch object.

    """
    with monkeypatch.context() as m:
        m.chdir(tmp_path)
        # Get test config
        infile = Path(__file__).parent / "data" / "gmd_mean_htcondor.yaml"
        # Read test config
        contents = yaml.load(infile)
        # Working directory
        contents["workdir"] = str(tmp_path.resolve())
        # Storage
        contents["storage"]["uri"] = str((tmp_path / "out.sqlite").resolve())
        # Write new test config
        outfile = tmp_path / "in.yaml"
        yaml.dump(contents, stream=outfile)
        # Queue command arguments
        queue_args = [
            str(outfile.resolve()),
            "--verbose",
            "debug",
        ]
        # Invoke queue command
        queue_result = runner.invoke(queue, queue_args)
        # Check
        assert queue_result.exit_code == 0


@pytest.mark.parametrize(
    "action, action_file",
    [
        (run, "partly_cloudy_agg_mean_tian.yml"),
        (queue, "gmd_mean_htcondor.yaml"),
    ],
)
def test_reset(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    action: Callable,
    action_file: str,
) -> None:
    """Test reset command.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    monkeypatch : pytest.MonkeyPatch
        The pytest.MonkeyPatch object.
    action : callable
        The parametrized action to perform.
    action_file : str
        The parametrized file for the action.

    """
    with monkeypatch.context() as m:
        m.chdir(tmp_path)
        # Get test config
        infile = Path(__file__).parent / "data" / action_file
        # Read test config
        contents = yaml.load(infile)
        # Working directory
        contents["workdir"] = str(tmp_path.resolve())
        # Storage
        contents["storage"]["uri"] = str((tmp_path / "out.sqlite").resolve())
        # Write new test config
        outfile = tmp_path / "in.yaml"
        yaml.dump(contents, stream=outfile)
        # Command arguments
        action_args = [
            str(outfile.resolve()),
            "--verbose",
            "debug",
        ]
        # Invoke command
        result = runner.invoke(action, action_args)
        # Check
        assert result.exit_code == 0

        # Reset arguments
        reset_args = [
            str(outfile.resolve()),
            "--verbose",
            "debug",
        ]
        # Run reset
        reset_result = runner.invoke(reset, reset_args)
        # Check
        assert reset_result.exit_code == 0


@pytest.mark.parametrize(
    "elements",
    [
        ("sub-01", "sub-02"),
        ("sub-03", "sub-04"),
    ],
)
def test_list_elements_stdout(
    elements: tuple[str, ...],
) -> None:
    """Test elements listing to stdout.

    Parameters
    ----------
    elements : tuple of str
        The parametrized elements for filtering.

    """
    # Get test config
    infile = Path(__file__).parent / "data" / "partly_cloudy_agg_mean_tian.yml"
    # List elements command arguments
    list_elements_args = [
        str(infile.absolute()),
        "--verbose",
        "debug",
        "--element",
        elements[0],
        "--element",
        elements[1],
    ]
    # Invoke list elements command
    list_elements_result = runner.invoke(list_elements, list_elements_args)
    # Check
    assert list_elements_result.exit_code == 0
    assert f"{elements[0]}\n{elements[1]}" in list_elements_result.stdout


@pytest.mark.parametrize(
    "elements",
    [
        ("sub-01", "sub-02"),
        ("sub-03", "sub-04"),
    ],
)
def test_list_elements_output_file(
    tmp_path: Path,
    elements: tuple[str, ...],
) -> None:
    """Test elements listing to output file.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    elements : tuple of str
        The parametrized elements for filtering.

    """
    # Get test config
    infile = Path(__file__).parent / "data" / "partly_cloudy_agg_mean_tian.yml"
    # Output file
    output_file = tmp_path / "elements.txt"
    # List elements command arguments
    list_elements_args = [
        str(infile.absolute()),
        "--verbose",
        "debug",
        "--element",
        elements[0],
        "--element",
        elements[1],
        "--output-file",
        str(output_file.resolve()),
    ]
    # Invoke list elements command
    list_elements_result = runner.invoke(list_elements, list_elements_args)
    # Check
    assert list_elements_result.exit_code == 0
    with open(output_file) as f:
        assert f"{elements[0]}\n{elements[1]}" == f.read()


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
