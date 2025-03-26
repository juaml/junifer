"""Provide class and functions for logging."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import os
import sys


if sys.version_info < (3, 12):  # pragma: no cover
    from distutils.version import LooseVersion
else:
    from looseversion import LooseVersion

import logging
import warnings
from pathlib import Path
from typing import ClassVar, NoReturn, Optional, Union
from warnings import warn

import datalad


__all__ = [
    "WrapStdOut",
    "configure_logging",
    "get_versions",
    "log_versions",
    "raise_error",
    "warn_with_log",
]


logger = logging.getLogger("JUNIFER")

# Set up datalad logger level to warning by default
datalad.log.lgr.setLevel(logging.WARNING)

_logging_types = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
}


# Copied over from stdlib and tweaked to our use-case.
def _showwarning(message, category, filename, lineno, file=None, line=None):
    s = warnings.formatwarning(message, category, filename, lineno, line)
    logger.warning(str(s))


# Overwrite warnings display to integrate with logging


def capture_warnings():
    """Capture warnings and log them."""
    warnings.showwarning = _showwarning


capture_warnings()


class WrapStdOut(logging.StreamHandler):
    """Dynamically wrap to sys.stdout.

    This makes packages that monkey-patch sys.stdout (e.g.doctest,
    sphinx-gallery) work properly.

    """

    def __getattr__(self, name: str) -> str:
        """Implement attribute fetch."""
        # Even more ridiculous than this class, this must be sys.stdout (not
        # just stdout) in order for this to work (tested on OSX and Linux)
        if hasattr(sys.stdout, name):
            return getattr(sys.stdout, name)
        else:  # pragma: no cover
            raise AttributeError(f"'file' object has not attribute '{name}'")


class ColorFormatter(logging.Formatter):
    """Color formatter for logging messages.

    Parameters
    ----------
    fmt : str
        The format string for the logging message.
    datefmt : str, optional
        The format string for the date.

    """

    BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

    COLORS: ClassVar[dict[str, int]] = {
        "WARNING": YELLOW,
        "INFO": GREEN,
        "DEBUG": BLUE,
        "CRITICAL": MAGENTA,
        "ERROR": RED,
    }

    RESET_SEQ: str = "\033[0m"
    COLOR_SEQ: str = "\033[1;%dm"
    BOLD_SEQ: str = "\033[1m"

    def __init__(
        self, fmt: str, datefmt: Optional[str] = None
    ) -> None:  # pragma: no cover
        """Initialize the ColorFormatter."""
        logging.Formatter.__init__(self, fmt, datefmt)

    def format(self, record: logging.LogRecord) -> str:  # pragma: no cover
        """Format the log record.

        Parameters
        ----------
        record : logging.LogRecord
            The log record to format.

        Returns
        -------
        str
            The formatted log record.

        """
        levelname = record.levelname
        if levelname in self.COLORS:
            levelname_color = (
                self.COLOR_SEQ % (30 + self.COLORS[levelname]) + levelname
            )
            record.levelname = levelname_color + self.RESET_SEQ
        return logging.Formatter.format(self, record)


def get_versions() -> dict:
    """Import stuff and get versions if module.

    Returns
    -------
    module_versions : dict
        The module names and corresponding versions.

    """
    # Setup dictionary to track versions of modules
    module_versions = {}
    for name, module in sys.modules.copy().items():
        # Bypassing sub-modules of packages and
        # allowing ruamel.yaml
        if "." in name and name != "ruamel.yaml":
            continue
        # Get version or None as string
        vstring = str(getattr(module, "__version__", None))
        # Get module version
        module_version = getattr(LooseVersion(vstring), "vstring", None)
        module_versions[name] = module_version
    return module_versions


def _close_handlers(logger: logging.Logger) -> None:  # pragma: no cover
    """Safely close relevant handlers for logger.

    Parameters
    ----------
    logger : logging.logger
        The logger to close handlers for.

    """
    for handler in list(logger.handlers):
        if isinstance(handler, (logging.FileHandler, logging.StreamHandler)):
            if isinstance(handler, logging.FileHandler):
                handler.close()
            logger.removeHandler(handler)


def log_versions() -> None:
    """Log versions of dependencies and junifer."""
    # Get versions of all found packages
    versions = get_versions()
    # Set packages to log
    pkgs_to_log = [
        "click",
        "numpy",
        "scipy",
        "datalad",
        "pandas",
        "nibabel",
        "nilearn",
        "sqlalchemy",
        "ruamel.yaml",
        "h5py",
        "tqdm",
        "templateflow",
        "lapy",
        "junifer_data",
        "junifer",
    ]
    # Log
    logger.info("===== Lib Versions =====")
    for pkg in pkgs_to_log:
        if pkg in versions:
            logger.info(f"{pkg}: {versions[pkg]}")
    logger.info("========================")


def _can_use_color(handler: logging.Handler) -> bool:  # pragma: no cover
    """Check if color can be used in the logging output.

    Parameters
    ----------
    handler : logging.Handler
        The logging handler to check for color support.

    Returns
    -------
    bool
        Whether color can be used in the logging output.

    """
    if isinstance(handler, logging.FileHandler):
        # Do not use colors in file handlers
        return False
    else:
        stream = handler.stream
        if hasattr(stream, "isatty") and stream.isatty():
            valid_terms = [
                "xterm-256color",
                "xterm-kitty",
                "xterm-color",
            ]
            this_term = os.getenv("TERM", None)
            if this_term is not None:
                if this_term in valid_terms:
                    return True
                if this_term.endswith("256color") or this_term.endswith("256"):
                    return True
                if this_term == "dumb" and os.getenv("CI", False):
                    return True
            if os.getenv("COLORTERM", False):
                return True
        # No TTY, no color
        return False


def configure_logging(
    level: Union[int, str] = "WARNING",
    fname: Optional[Union[str, Path]] = None,
    overwrite: Optional[bool] = None,
    output_format=None,
    level_datalad: Union[int, str, None] = None,
) -> None:
    """Configure the logging functionality.

    Parameters
    ----------
    level : int or {"DEBUG", "INFO", "WARNING", "ERROR"}
        The level of the messages to print. If string, it will be interpreted
        as elements of logging (default "WARNING").
    fname : str or pathlib.Path, optional
        Filename of the log to print to. If None, stdout is used
        (default None).
    overwrite : bool, optional
        Overwrite the log file (if it exists). Otherwise, statements
        will be appended to the log (default). None is the same as False,
        but additionally raises a warning to notify the user that log
        entries will be appended (default None).
    output_format : str, optional
        Format of the output messages. See the following for examples:
        https://docs.python.org/dev/howto/logging.html
        e.g., ``"%(asctime)s - %(levelname)s - %(message)s"``.
        If None, default string format is used
        (default ``"%(asctime)s - %(name)s - %(levelname)s - %(message)s"``).
    level_datalad : int or {"DEBUG", "INFO", "WARNING", "ERROR"}, optional
        The level of the messages to print for datalad. If string, it will be
        interpreted as elements of logging. If None, it will be set as the
        ``level`` parameter (default None).

    """
    _close_handlers(logger)  # close relevant logger handlers

    # Set logging level
    if isinstance(level, str):
        level = _logging_types[level]

    # Set logging output handler
    if fname is not None:
        # Convert str to Path
        if not isinstance(fname, Path):
            fname = Path(fname)
        if fname.exists() and overwrite is None:
            warn(
                f"File ({fname.absolute()!s}) exists. "
                "Messages will be appended. Use overwrite=True to "
                "overwrite or overwrite=False to avoid this message.",
                stacklevel=2,
            )
            overwrite = False
        mode = "w" if overwrite else "a"
        lh = logging.FileHandler(fname, mode=mode)
    else:
        lh = logging.StreamHandler(WrapStdOut())  # type: ignore

    # Set logging format
    if output_format is None:
        output_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    if _can_use_color(lh):  # pragma: no cover
        formatter = ColorFormatter(fmt=output_format)
    else:
        formatter = logging.Formatter(fmt=output_format)

    lh.setFormatter(formatter)  # set formatter
    logger.setLevel(level)  # set level

    # Set datalad logging level accordingly
    if level_datalad is not None:
        if isinstance(level_datalad, str):
            level_datalad = _logging_types[level_datalad]
    else:
        level_datalad = level
    datalad.log.lgr.setLevel(level_datalad)  # set level for datalad

    logger.addHandler(lh)  # set handler
    log_versions()  # log versions of installed packages


def raise_error(
    msg: str,
    klass: type[Exception] = ValueError,
    exception: Optional[Exception] = None,
) -> NoReturn:
    """Raise error, but first log it.

    Parameters
    ----------
    msg : str
        The message for the exception.
    klass : subclass of Exception, optional
        The subclass of Exception to raise using (default ValueError).
    exception : Exception, optional
        The original exception to follow up on (default None).

    """
    logger.error(msg)
    if exception is not None:
        raise klass(msg) from exception
    else:
        raise klass(msg)


def warn_with_log(
    msg: str, category: Optional[type[Warning]] = RuntimeWarning
) -> None:
    """Warn, but first log it.

    Parameters
    ----------
    msg : str
        Warning message.
    category : subclass of Warning, optional
        The warning subclass (default RuntimeWarning).

    """
    warn(msg, category=category, stacklevel=2)
