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

    """

    def __init__(self, workdir: Optional[Union[str, Path]] = None) -> None:
        """Initialize the class."""
        # Check if workdir is already set
        if not hasattr(self, "_workdir"):
            # Check and set topmost level directory if not provided
            if workdir is None:
                workdir = Path(tempfile.gettempdir())
            # Convert str to Path
            if isinstance(workdir, str):
                workdir = Path(workdir)
            logger.debug(f"Setting working directory at {workdir.resolve()!s}")
            self._workdir = workdir

        # Initialize root temporary directory
        self._root_temp_dir: Optional[Path] = None

    def __del__(self) -> None:
        """Destructor."""
        # Remove root temporary directory
        if self._root_temp_dir is not None:
            shutil.rmtree(self._root_temp_dir, ignore_errors=True)

    @property
    def workdir(self) -> Path:
        """Get working directory."""
        return self._workdir

    @workdir.setter
    def workdir(self, value: Path) -> None:
        """Set working directory."""
        logger.debug(f"Changing working directory to {value}")
        self._workdir = value

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
        if self._root_temp_dir is None:
            logger.debug(
                f"Setting up temporary directory under {self._workdir}"
            )
            self._root_temp_dir = Path(tempfile.mkdtemp(dir=self._workdir))

        logger.debug(f"Creating temporary directory at {self._root_temp_dir}")
        return Path(
            tempfile.mkdtemp(
                dir=self._root_temp_dir, prefix=prefix, suffix=suffix
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
