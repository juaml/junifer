"""Provide a work directory manager class to be used by pipeline components."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
#          Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

import shutil
import tempfile
from pathlib import Path
from typing import Optional, Union

from ..utils import logger
from .singleton import singleton


@singleton
class WorkDirManager:
    """Class for working directory manager.

    This class is a singleton and is used for managing temporary and working
    directories used across the pipeline by datagrabbers, preprocessors,
    markers and so on. It maintains a single super-directory and provides
    directories on-demand and cleans after itself thus keeping the user
    filesystem clean.

    Parameters
    ----------
    workdir : str or pathlib.Path, optional
        The path to the super-directory. If None, "TMPDIR/junifer" is used
        where TMPDIR is the platform-dependent temporary directory.

    Attributes
    ----------
    workdir : pathlib.Path
        The path to the working directory.
    root_tempdir : pathlib.Path or None
        The path to the root temporary directory.

    """

    def __init__(self, workdir: Optional[Union[str, Path]] = None) -> None:
        """Initialize the class."""
        self._workdir = workdir
        self._root_tempdir = None

        self._set_default_workdir()

    def _set_default_workdir(self) -> None:
        """Set the default working directory if not set already."""
        # Check and set topmost level directory if not provided
        if self._workdir is None:
            self._workdir = Path(tempfile.gettempdir()) / "junifer"
            # Create directory if not found
            if not self._workdir.is_dir():
                logger.debug(
                    "Creating working directory at "
                    f"{self._workdir.resolve()!s}"
                )
                self._workdir.mkdir(parents=True)
            logger.debug(
                f"Setting working directory to {self._workdir.resolve()!s}"
            )

    def __del__(self) -> None:
        """Destructor."""
        self._cleanup()

    def _cleanup(self) -> None:
        """Clean up the temporary directories."""
        # Remove root temporary directory
        if self._root_tempdir is not None:
            logger.debug(
                "Deleting temporary directory at "
                f"{self._root_tempdir.resolve()!s}"
            )
            shutil.rmtree(self._root_tempdir, ignore_errors=True)
            self._root_tempdir = None

    @property
    def workdir(self) -> Path:
        """Get working directory."""
        return self._workdir  # type: ignore

    @workdir.setter
    def workdir(self, path: Union[str, Path]) -> None:
        """Set working directory.

        The directory path is created if it doesn't exist yet.

        Parameters
        ----------
        path : str or pathlib.Path
            The path to the working directory.

        """
        # Check if existing working directory is same or not;
        # if not, then clean up
        if self._workdir != Path(path):
            self._cleanup()
        # Set working directory
        self._workdir = Path(path)
        logger.debug(
            f"Changing working directory to {self._workdir.resolve()!s}"
        )
        # Create directory if not found
        if not self._workdir.is_dir():
            logger.debug(
                f"Creating working directory at {self._workdir.resolve()!s}"
            )
            self._workdir.mkdir(parents=True)

    @property
    def root_tempdir(self) -> Optional[Path]:
        """Get root temporary directory."""
        return self._root_tempdir

    def get_tempdir(
        self, prefix: Optional[str] = None, suffix: Optional[str] = None
    ) -> Path:
        """Get a temporary directory.

        Parameters
        ----------
        prefix : str
            The temporary directory prefix. If None, a default prefix is used.
        suffix : str
            The temporary directory suffix. If None, no suffix is added.

        Returns
        -------
        pathlib.Path
            The path to the temporary directory.

        """
        # Create root temporary directory if not created already
        if self._root_tempdir is None:
            logger.debug(
                "Setting up temporary directory under "
                f"{self._workdir.resolve()!s}"  # type: ignore
            )
            self._root_tempdir = Path(tempfile.mkdtemp(dir=self._workdir))

        logger.debug(
            f"Creating temporary directory at {self._root_tempdir.resolve()!s}"
        )
        return Path(
            tempfile.mkdtemp(
                dir=self._root_tempdir, prefix=prefix, suffix=suffix
            )
        )

    def delete_tempdir(self, tempdir: Path) -> None:
        """Delete a temporary directory.

        Parameters
        ----------
        tempdir : pathlib.Path
            The temporary directory path to be deleted.

        """
        logger.debug(f"Deleting temporary directory at {tempdir}")
        shutil.rmtree(tempdir, ignore_errors=True)
