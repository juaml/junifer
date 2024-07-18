"""Provide tests for logging."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Sami Hamdan <s.hamdan@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import logging
from pathlib import Path

import pytest

from junifer.utils.logging import (
    _close_handlers,
    configure_logging,
    get_versions,
    log_versions,
    logger,
    raise_error,
    warn_with_log,
)


def test_get_versions() -> None:
    """Test version info fetch for modules."""
    module_versions = get_versions()
    assert "junifer" in module_versions.keys()


def test_log_versions(caplog: pytest.LogCaptureFixture) -> None:
    """Test logging of dependency and junifer versions.

    Parameters
    ----------
    caplog : pytest.LogCaptureFixture
        The pytest.LogCaptureFixture object.

    """
    # Set log capturing at INFO
    with caplog.at_level(logging.INFO):
        # Log versions
        log_versions()
        # Check logging levels
        for record in caplog.records:
            assert record.levelname not in ("DEBUG", "WARNING", "ERROR")
            assert record.levelname == "INFO"
        # Check logging message
        assert "junifer" in caplog.text


def test_log_file(tmp_path: Path) -> None:
    """Test logging to a file.

    tmp_path : Path
        The path to the test directory.

    """
    configure_logging(fname=tmp_path / "test1.log")
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warn message")
    logger.error("Error message")
    _close_handlers(logger)
    with open(tmp_path / "test1.log") as f:
        lines = f.readlines()
        assert not any("Debug message" in line for line in lines)
        assert not any("Info message" in line for line in lines)
        assert any("Warn message" in line for line in lines)
        assert any("Error message" in line for line in lines)

    configure_logging(fname=tmp_path / "test2.log", level="INFO")
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warn message")
    logger.error("Error message")
    _close_handlers(logger)
    with open(tmp_path / "test2.log") as f:
        lines = f.readlines()
        assert not any("Debug message" in line for line in lines)
        assert any("Info message" in line for line in lines)
        assert any("Warn message" in line for line in lines)
        assert any("Error message" in line for line in lines)

    configure_logging(fname=tmp_path / "test3.log", level="WARNING")
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warn message")
    logger.error("Error message")
    _close_handlers(logger)
    with open(tmp_path / "test3.log") as f:
        lines = f.readlines()
        assert not any("Debug message" in line for line in lines)
        assert not any("Info message" in line for line in lines)
        assert any("Warn message" in line for line in lines)
        assert any("Error message" in line for line in lines)

    configure_logging(fname=tmp_path / "test4.log", level="ERROR")
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warn message")
    logger.error("Error message")
    with open(tmp_path / "test4.log") as f:
        lines = f.readlines()
        assert not any("Debug message" in line for line in lines)
        assert not any("Info message" in line for line in lines)
        assert not any("Warn message" in line for line in lines)
        assert any("Error message" in line for line in lines)

    with pytest.warns(UserWarning, match="to avoid this message"):
        configure_logging(fname=tmp_path / "test4.log", level="WARNING")
        logger.debug("Debug2 message")
        logger.info("Info2 message")
        logger.warning("Warn2 message")
        logger.error("Error2 message")
        with open(tmp_path / "test4.log") as f:
            lines = f.readlines()
            assert not any("Debug message" in line for line in lines)
            assert not any("Info message" in line for line in lines)
            assert not any("Warn message" in line for line in lines)
            assert any("Error message" in line for line in lines)
            assert not any("Debug2 message" in line for line in lines)
            assert not any("Info2 message" in line for line in lines)
            assert any("Warn2 message" in line for line in lines)
            assert any("Error2 message" in line for line in lines)

    configure_logging(
        fname=tmp_path / "test4.log", level="WARNING", overwrite=True
    )
    logger.debug("Debug3 message")
    logger.info("Info3 message")
    logger.warning("Warn3 message")
    logger.error("Error3 message")
    with open(tmp_path / "test4.log") as f:
        lines = f.readlines()
        assert not any("Debug message" in line for line in lines)
        assert not any("Info message" in line for line in lines)
        assert not any("Warn message" in line for line in lines)
        assert not any("Error message" in line for line in lines)
        assert not any("Debug2 message" in line for line in lines)
        assert not any("Info2 message" in line for line in lines)
        assert not any("Warn2 message" in line for line in lines)
        assert not any("Error2 message" in line for line in lines)
        assert not any("Debug3 message" in line for line in lines)
        assert not any("Info3 message" in line for line in lines)
        assert any("Warn3 message" in line for line in lines)
        assert any("Error3 message" in line for line in lines)

    # This should raise a warning (test that it was raised)
    with pytest.warns(RuntimeWarning, match=r"Warn raised"):
        warn_with_log("Warn raised")

    # This should log the warning (workaround for pytest messing with logging)
    from junifer.utils.logging import capture_warnings

    capture_warnings()

    warn_with_log("Warn raised 2")
    with pytest.raises(ValueError, match=r"Error raised"):
        raise_error("Error raised")
    with open(tmp_path / "test4.log") as f:
        lines = f.readlines()
        assert any("Warn raised" in line for line in lines)
        assert any("Error raised" in line for line in lines)


def test_log_stdout(caplog: pytest.LogCaptureFixture) -> None:
    """Test logging to stdout.

    Parameters
    ----------
    caplog : pytest.LogCaptureFixture
        The pytest.LogCaptureFixture object.

    """
    configure_logging()
    logger.info("Testing")
    for record in caplog.records:
        assert record.levelname == "INFO"


def test_lib_logging(tmp_path: Path) -> None:
    """Test logging versions.

    tmp_path : Path
        The path to the test directory.

    """
    # Import third-party packages
    import numpy  # noqa: F401
    import pandas  # noqa: F401

    log_file_path = tmp_path / "test_lib_logging.log"
    configure_logging(fname=log_file_path, level="INFO")
    logger.info("first message")
    with open(log_file_path) as f:
        lines = f.readlines()
        assert any("numpy" in line for line in lines)
        assert any("pandas" in line for line in lines)
        assert any("junifer" in line for line in lines)


def test_raise_error(caplog: pytest.LogCaptureFixture) -> None:
    """Test logging and raising error.

    Parameters
    ----------
    caplog : pytest.LogCaptureFixture
        The pytest.LogCaptureFixture object.

    """
    with pytest.raises(ValueError, match="test error"):
        raise_error(msg="test error")
        for record in caplog.records:
            assert record.levelname == "ERROR"


def test_warn_with_log(caplog: pytest.LogCaptureFixture) -> None:
    """Test logging and warning.

    Parameters
    ----------
    caplog : pytest.LogCaptureFixture
        The pytest.LogCaptureFixture object.

    """
    with pytest.warns(RuntimeWarning, match="test warning"):
        warn_with_log("test warning")
        for record in caplog.records:
            assert record.levelname == "WARNING"
