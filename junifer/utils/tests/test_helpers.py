"""Provide tests for helper functions."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import logging

import pytest

from junifer.utils.helpers import check_standardize, run_ext_cmd


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


@pytest.mark.parametrize("value", ["zscore_sample", "psc", None])
def test_check_standardize(value: str | None) -> None:
    """Test check_standardize with valid values.

    Parameters
    ----------
    value : str or None
        The parametrized value.

    """
    assert check_standardize(value) == value


@pytest.mark.parametrize(
    "value, replacement",
    [
        (True, "'zscore_sample' instead of True"),
        (False, "None instead of False"),
    ],
)
def test_check_standardize_bool(value: bool, replacement: str) -> None:
    """Test check_standardize error for booleans.

    Parameters
    ----------
    value : bool
        The parametrized value.
    replacement : str
        The parametrized replacement in the error message.

    """
    with pytest.raises(ValueError, match=replacement):
        check_standardize(value)
