"""Provide tests for CLI parser."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import sys
from pathlib import Path

import pytest

from junifer.cli.parser import parse_yaml


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
    assert contents["with"] == ["numpy"]
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


def test_parse_yaml_with_wrong_path(tmp_path: Path) -> None:
    """Test YAML parsing with wrong paths in with.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    t_tmp_path = tmp_path / "test_relative_with"
    # Write yaml that includes a relative path
    yaml_path = t_tmp_path / "yamls"
    yaml_path.mkdir(exist_ok=True, parents=True)
    yaml_fname = yaml_path / "test_parse_yaml_wrong_path.yaml"

    yaml_fname.write_text("foo: bar\nwith:\n  -  missingt.py\n  - scipy\n")

    # Check test file
    with pytest.raises(ValueError, match="does not exist"):
        parse_yaml(yaml_fname)


def test_parse_yaml_relative_path(tmp_path: Path) -> None:
    """Test YAML parsing with relative paths in with.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    t_tmp_path = tmp_path / "test_relative_with"

    # Write .py to include
    py_path = t_tmp_path / "external"
    py_path.mkdir(exist_ok=True, parents=True)
    py_fname = py_path / "first.py"
    py_fname.write_text("import numpy as np\n")

    # Write yaml that includes a relative path
    yaml_path = t_tmp_path / "yamls"
    yaml_path.mkdir(exist_ok=True, parents=True)
    yaml_fname = yaml_path / "test_parse_yaml_relative_path.yaml"

    yaml_fname.write_text(
        "foo: bar\nwith:\n  - ../external/first.py\n  - scipy\n"
    )

    # Check test file
    parse_yaml(yaml_fname)


def test_parse_yaml_absolute_path(tmp_path: Path) -> None:
    """Test YAML parsing with absolute paths in with.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    t_tmp_path = tmp_path / "test_relative_with"

    # Write .py to include
    py_path = t_tmp_path / "external"
    py_path.mkdir(exist_ok=True, parents=True)
    py_fname = py_path / "first.py"
    py_fname.write_text("import numpy as np\n")

    # Write yaml that includes a relative path
    yaml_path = t_tmp_path / "yamls"
    yaml_path.mkdir(exist_ok=True, parents=True)
    yaml_fname = yaml_path / "test_parse_yaml_relative_path.yaml"

    yaml_fname.write_text(
        f"foo: bar\nwith:\n  - {py_fname.absolute()}\n  - scipy\n"
    )

    # Check test file
    parse_yaml(yaml_fname)


def test_parse_storage_uri_relative(tmp_path: Path) -> None:
    """Test YAML parsing with storage and relative URI.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    fname = tmp_path / "test_parse_yaml_with_storage_uri.yaml"
    fname.write_text("foo: bar\nwith: numpy\nstorage:\n  uri: test.db\n")

    contents = parse_yaml(fname)
    assert "foo" in contents
    assert contents["foo"] == "bar"
    assert "storage" in contents
    assert "uri" in contents["storage"]
    assert contents["storage"]["uri"] == str(tmp_path / "test.db")

    fname = tmp_path / "test_parse_yaml_with_storage_uri.yaml"
    fname.write_text(
        "foo: bar\nwith: numpy\nstorage:\n  uri: ../another/test.db\n"
    )

    contents = parse_yaml(fname)
    assert "foo" in contents
    assert contents["foo"] == "bar"
    assert "storage" in contents
    assert "uri" in contents["storage"]
    assert contents["storage"]["uri"] == str(
        (tmp_path / "../another/test.db").resolve()
    )

    fname = tmp_path / "test_parse_yaml_with_storage_uri.yaml"
    fname.write_text(
        "foo: bar\nwith: numpy\nstorage:\n  uri: /absolute/test.db\n"
    )

    contents = parse_yaml(fname)
    assert "foo" in contents
    assert contents["foo"] == "bar"
    assert "storage" in contents
    assert "uri" in contents["storage"]
    assert contents["storage"]["uri"] == "/absolute/test.db"

    # Just to trick coverage
    fname = tmp_path / "test_parse_yaml_with_storage_uri.yaml"
    fname.write_text("foo: bar\nwith: numpy\nstorage:\n  kind: SomeStorage\n")

    contents = parse_yaml(fname)
    assert "foo" in contents
    assert contents["foo"] == "bar"
    assert "storage" in contents
