"""Provide tests for helper functions."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import logging

import pytest

from junifer.utils.helpers import run_ext_cmd


def test_run_ext_cmd_success(caplog: pytest.LogCaptureFixture) -> None:
    """Test external command run success.

    Parameters
    ----------
    caplog : pytest.LogCaptureFixture
        The pytest.LogCaptureFixture object.

    """
    # Set log capturing at INFO
    with caplog.at_level(logging.INFO):
        # Run external command
        run_ext_cmd(name="pwd", cmd=["pwd"])
        # Check logging message
        assert "executed" in caplog.text
        assert "succeeded" in caplog.text


def test_run_ext_cmd_failure() -> None:
    """Test external command run failure."""
    with pytest.raises(RuntimeError, match="failed"):
        # Run external command
        run_ext_cmd(name="flymetothemoon", cmd=["flymetothemoon"])
