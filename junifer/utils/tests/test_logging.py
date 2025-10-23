"""Provide tests for logging."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Sami Hamdan <s.hamdan@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import logging

import pytest

from junifer.utils.logging import (
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
        assert len(caplog.records) != 0
        # Check logging levels
        for record in caplog.records:
            assert record.levelname not in ("DEBUG", "WARNING", "ERROR")
            assert record.levelname == "INFO"
        # Check logging message
        assert "numpy" in caplog.text
        assert "pandas" in caplog.text
        assert "junifer" in caplog.text


def test_log_stdout(caplog: pytest.LogCaptureFixture) -> None:
    """Test logging to stdout.

    Parameters
    ----------
    caplog : pytest.LogCaptureFixture
        The pytest.LogCaptureFixture object.

    """
    # Set log capturing at INFO
    with caplog.at_level(logging.INFO):
        logger.info("Testing")
        assert len(caplog.records) == 1
        for record in caplog.records:
            assert record.levelname == "INFO"
        assert "Testing" in caplog.text


def test_raise_error(caplog: pytest.LogCaptureFixture) -> None:
    """Test logging and raising error.

    Parameters
    ----------
    caplog : pytest.LogCaptureFixture
        The pytest.LogCaptureFixture object.

    """
    with pytest.raises(ValueError, match="test error"):
        raise_error(msg="test error")
        assert len(caplog.records) == 1
        for record in caplog.records:
            assert record.levelname == "ERROR"
        assert "test error" in caplog.text


def test_warn_with_log(caplog: pytest.LogCaptureFixture) -> None:
    """Test logging and warning.

    Parameters
    ----------
    caplog : pytest.LogCaptureFixture
        The pytest.LogCaptureFixture object.

    """
    # Explicitly needed as pytest messes with logging
    from junifer.utils.logging import capture_warnings

    capture_warnings()
    # Check logging
    warn_with_log("test warning")
    assert len(caplog.records) == 1
    for record in caplog.records:
        assert record.levelname == "WARNING"
    assert "test warning" in caplog.text
    # Check normal warning capture
    with pytest.warns(RuntimeWarning, match="test warning 2"):
        warn_with_log("test warning 2")
