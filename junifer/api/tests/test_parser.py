"""Provide tests for parser."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import sys
from pathlib import Path

import pytest

from junifer.api.parser import parse_yaml


def test_parse_yaml_failure() -> None:
    """Test YAML parsing failure."""
    with pytest.raises(ValueError, match="does not exist"):
        parse_yaml("foo.yaml")


def test_parse_yaml_success(tmp_path: Path) -> None:
    """Test YAML parsing success.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    # Write test file
    fname = tmp_path / "test_parse_yaml_success.yaml"
    fname.write_text("foo: bar")
    # Check test file
    contents = parse_yaml(fname)
    assert "foo" in contents
    assert contents["foo"] == "bar"


def test_parse_yaml_success_with_module_autoload(tmp_path: Path) -> None:
    """Test YAML parsing with single module autoload success.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    # Write test file
    fname = tmp_path / "test_parse_yaml_with_single_module_autoload.yaml"
    fname.write_text("foo: bar\nwith: numpy")
    # Check test file
    contents = parse_yaml(fname)
    assert "foo" in contents
    assert contents["foo"] == "bar"
    assert "with" in contents
    assert contents["with"] == "numpy"
    assert "numpy" in sys.modules
    assert "junifer.configs.wrong_config" not in sys.modules


def test_parse_yaml_failure_with_multi_module_autoload(tmp_path: Path) -> None:
    """Test YAML parsing with multi module autoload failure.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    # Write test file
    fname = tmp_path / "test_parse_yaml_with_multi_module_autoload.yaml"
    fname.write_text(
        "foo: bar\nwith:\n  - numpy\n  - junifer.testing.wrong_config"
    )
    # Check test file
    with pytest.raises(ImportError, match="wrong_config"):
        parse_yaml(fname)
