"""Provide class and functions for logging."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import sys


if sys.version_info < (3, 12):  # pragma: no cover
    from distutils.version import LooseVersion
else:
    from looseversion import LooseVersion

import logging
import logging.config
import warnings
from typing import NoReturn, Optional, Union
from warnings import warn

import datalad
import structlog


__all__ = [
    "configure_logging",
    "get_versions",
    "log_versions",
    "raise_error",
    "warn_with_log",
]


# Common processors for stdlib and structlog
_timestamper = structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S")


def _remove_datalad_message(_, __, event_dict):
    """Clean datalad records."""
    if "message" in event_dict:
        event_dict.pop("message")
    return event_dict


_pre_chain = [
    structlog.stdlib.add_log_level,
    structlog.stdlib.add_logger_name,
    structlog.stdlib.ExtraAdder(),
    _timestamper,
    _remove_datalad_message,
]


def _configure_stdlib(level: int = logging.WARNING) -> None:
    """Configure stdlib logging.

    Parameters
    ----------
    level : int, optional
        The logging level (default 30).

    """
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "console": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processors": [
                        structlog.stdlib.add_logger_name,
                        structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                        structlog.dev.ConsoleRenderer(
                            colors=sys.stdout.isatty() and sys.stderr.isatty()
                        ),
                    ],
                    "foreign_pre_chain": _pre_chain,
                },
            },
            "handlers": {
                "default": {
                    "level": level,
                    "class": "logging.StreamHandler",
                    "formatter": "console",
                },
            },
            "loggers": {
                "": {
                    "handlers": ["default"],
                    "level": level,
                    "propagate": True,
                },
            },
        }
    )


# Initial logging setup
_configure_stdlib()
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        _timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = logging.getLogger("junifer")

# Remove datalad logger handlers to avoid duplicate logging
_datalad_lgr_hdlrs = datalad.log.lgr.handlers
for h in _datalad_lgr_hdlrs:
    datalad.log.lgr.removeHandler(h)

_logging_types = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
}


# Copied over from stdlib and tweaked to our use-case.
def _showwarning(message, category, filename, lineno, file=None, line=None):
    s = warnings.formatwarning(message, category, filename, lineno, line)
    logger.warning(s)


# Overwrite warnings display to integrate with logging
def capture_warnings():
    """Capture warnings and log them."""
    warnings.showwarning = _showwarning


capture_warnings()


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
    hdlrs = logger.handlers
    for h in hdlrs:
        logger.removeHandler(h)


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


def configure_logging(
    level: Union[int, str] = "WARNING",
    level_datalad: Union[int, str, None] = None,
) -> None:
    """Configure the logging functionality.

    Parameters
    ----------
    level : int or {"DEBUG", "INFO", "WARNING", "ERROR"}
        The level of the messages to print. If string, it will be interpreted
        as elements of logging (default "WARNING").
    level_datalad : int or {"DEBUG", "INFO", "WARNING", "ERROR"}, optional
        The level of the messages to print for datalad. If string, it will be
        interpreted as elements of logging. If None, it will be set as the
        ``level`` parameter (default None).

    """
    _close_handlers(logger)
    # Set logging level
    if isinstance(level, str):
        level = _logging_types[level]

    _configure_stdlib(level)
    # Set datalad logging level accordingly
    if level_datalad is not None:
        if isinstance(level_datalad, str):
            level_datalad = _logging_types[level_datalad]
    else:
        level_datalad = level
    datalad.log.lgr.setLevel(level_datalad)

    log_versions()


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
