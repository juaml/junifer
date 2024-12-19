"""Provide abstract base class for datalad-based DataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import atexit
import os
import tempfile
from pathlib import Path
from typing import Optional, Union

import datalad
import datalad.api as dl
from datalad.support.exceptions import IncompleteResultsError
from datalad.support.gitrepo import GitRepo

from ..pipeline import WorkDirManager
from ..typing import Element
from ..utils import config, logger, raise_error, warn_with_log
from .base import BaseDataGrabber


__all__ = ["DataladDataGrabber"]


class DataladDataGrabber(BaseDataGrabber):
    """Abstract base class for datalad-based data fetching.

    Defines a DataGrabber that gets data from a datalad sibling.

    Parameters
    ----------
    rootdir : str or pathlib.Path, optional
        The path within the datalad dataset to the root directory
        (default ".").
    datadir : str or pathlib.Path or None, optional
        That directory where the datalad dataset will be cloned. If None,
        the datalad dataset will be cloned into a temporary directory
        (default None).
    uri : str or None, optional
        URI of the datalad sibling (default None).
    **kwargs
        Keyword arguments passed to superclass.

    Methods
    -------
    install:
        Installs (clones) the datalad dataset into the ``datadir``. This method
        is called automatically when the datagrabber is used within a context.
    remove:
        Removes the datalad dataset from the ``datadir``. This method is called
        automatically when the datagrabber is used within a context.

    See Also
    --------
    BaseDataGrabber:
        Abstract base class for DataGrabber.
    PatternDataGrabber:
        Concrete implementation for pattern-based data fetching.
    PatternDataladDataGrabber:
        Concrete implementation for pattern and datalad based data fetching.

    Notes
    -----
    This class is intended to be used as a superclass of a subclass
    with multiple inheritance.

    """

    def __init__(
        self,
        rootdir: Union[str, Path] = ".",
        datadir: Union[str, Path, None] = None,
        uri: Optional[str] = None,
        **kwargs,
    ):
        if datadir is None:
            logger.info("`datadir` is None, creating a temporary directory")
            # Create temporary directory
            tmpdir = WorkDirManager().get_tempdir(prefix="datalad")
            self._tmpdir = tmpdir
            datadir = tmpdir / "datadir"
            datadir.mkdir(parents=True, exist_ok=False)
            logger.info(f"`datadir` set to {datadir}")
            cache_dir = tmpdir / ".datalad_cache"
            sockets_dir = cache_dir / "sockets"
            locks_dir = cache_dir / "locks"
            sockets_dir.mkdir(parents=True, exist_ok=False)
            locks_dir.mkdir(parents=True, exist_ok=False)
            logger.debug(f"Setting datalad cache to {cache_dir}")
            os.environ["DATALAD_LOCATIONS_CACHE"] = cache_dir.as_posix()
            os.environ["DATALAD_LOCATIONS_SOCKETS"] = sockets_dir.as_posix()
            os.environ["DATALAD_LOCATIONS_LOCKS"] = locks_dir.as_posix()
            datalad.cfg.reload()
            logger.debug(
                "Datalad cache set to "
                f"{datalad.cfg.get('datalad.locations.cache')}"
            )
            logger.debug(
                "Datalad sockets set to "
                f"{datalad.cfg.get('datalad.locations.sockets')}"
            )
            logger.debug(
                "Datalad locks set to "
                f"{datalad.cfg.get('datalad.locations.locks')}"
            )
            atexit.register(self._rmtmpdir)
        # TODO: uri can be converted to a positional argument
        if uri is None:
            raise_error("`uri` must be provided")

        super().__init__(datadir=datadir, **kwargs)
        logger.debug("Initializing DataladDataGrabber")
        logger.debug(f"\turi = {uri}")
        logger.debug(f"\t_rootdir = {rootdir}")
        self.uri = uri
        self._rootdir = rootdir
        # Flag to indicate if the dataset was cloned before and it might be
        # dirty
        self.datalad_dirty = False

    def __del__(self) -> None:
        """Destructor."""
        if hasattr(self, "_tmpdir"):
            self._rmtmpdir()

    def _rmtmpdir(self) -> None:
        """Remove temporary directory if it exists."""
        if self._tmpdir.exists():
            logger.debug("Removing temporary directory")
            WorkDirManager().delete_tempdir(self._tmpdir)

    @property
    def datadir(self) -> Path:
        """Get data directory path.

        Returns
        -------
        pathlib.Path
            Path to the data directory.

        """
        return super().datadir / self._rootdir

    def _get_dataset_id_remote(self) -> tuple[str, bool]:
        """Get the dataset ID from the remote.

        Returns
        -------
        str
            The dataset ID.
        bool
            Whether the dataset is dirty.

        Raises
        ------
        ValueError
            If the dataset ID cannot be obtained from the remote.

        """
        remote_id = None
        is_dirty = False
        with tempfile.TemporaryDirectory() as tmpdir:
            if not config.get("datagrabber.skipidcheck", False):
                logger.debug(f"Querying {self.uri} for dataset ID")
                repo = GitRepo.clone(
                    self.uri, path=tmpdir, clone_options=["-n", "--depth=1"]
                )
                repo.checkout(name=".datalad/config", options=["HEAD"])
                remote_id = repo.config.get("datalad.dataset.id", None)
                logger.debug(f"Got remote dataset ID = {remote_id}")

                if not config.get("datagrabber.skipdirtycheck", False):
                    is_dirty = repo.dirty
                else:
                    logger.debug("Skipping dirty check")
                    is_dirty = False
            else:
                logger.debug("Skipping dataset ID check")
                remote_id = self._dataset.id
                is_dirty = False
            logger.debug(
                f"Remote dataset is {'' if is_dirty else 'not'} dirty"
            )
        if remote_id is None:
            raise_error("Could not get dataset ID from remote")
        return remote_id, is_dirty

    def _dataset_get(self, out: dict) -> dict:
        """Get the dataset found from the path in ``out``.

        Parameters
        ----------
        out : dict
            The dictionary from which path need to be searched.

        Returns
        -------
        dict
            The unmodified input dictionary.

        Raises
        ------
        datalad.support.exceptions.IncompleteResultsError
            If there is a datalad-related problem while fetching data.

        """
        to_get = []
        for type_val in out.values():
            # Conditional for list dtype vals like Warp
            if isinstance(type_val, list):
                for entry in type_val:
                    for k, v in entry.items():
                        if k == "path":
                            to_get.append(v)
            else:
                # Iterate to check for nested "types" like mask
                for k, v in type_val.items():
                    # Add base data type path
                    if k == "path":
                        to_get.append(v)
                    # Add nested data type path
                    if isinstance(v, dict) and "path" in v:
                        to_get.append(v["path"])

        if len(to_get) > 0:
            logger.debug(f"Getting {len(to_get)} files using datalad:")
            for fname in to_get:
                logger.debug(f"\t: {fname}")

            try:
                dl_out = self._dataset.get(to_get, result_renderer="disabled")
            except IncompleteResultsError as e:
                raise_error(f"Failed to get from dataset: {e.failed}")
            if not self._was_cloned:
                # If the dataset was already installed, check that the
                # file was actually downloaded to avoid removing a
                # file that was already there.
                for t_out in dl_out:
                    t_path = Path(t_out["path"])
                    if t_out["status"] == "ok":
                        logger.debug(f"File {t_path} downloaded")
                        self._got_files.append(t_path)
                    elif t_out["status"] == "notneeded":
                        logger.debug(f"File {t_path} was already present")
                    else:
                        raise_error(f"File download failed: {t_out}")
            logger.debug("Get done")

        return out

    def install(self) -> None:
        """Install the datalad dataset into the ``datadir``.

        Raises
        ------
        ValueError
            If the dataset is already installed but with a different ID.
        datalad.support.exceptions.IncompleteResultsError
            If there is a datalad-related problem while cloning dataset.

        """
        isinstalled = dl.Dataset(self._datadir).is_installed()
        if isinstalled:
            logger.debug("Dataset already installed")
            self._got_files = []
            self._dataset: dl.Dataset = dl.Dataset(self._datadir)

            # Check if dataset is already installed with a different ID
            remote_id, is_dirty = self._get_dataset_id_remote()
            if remote_id != self._dataset.id:
                raise_error(
                    "Dataset already installed but with a different "
                    f"ID: {self._dataset.id} (local) != {remote_id} (remote)"
                )

            # Conditional reporting on dataset dirtiness
            self.datalad_dirty = is_dirty
            if self.datalad_dirty:
                warn_with_log(
                    "At least one file is not clean, "
                    f"marking dataset (id: {self._dataset.id}) as dirty."
                )
            else:
                logger.debug(f"Dataset (id: {self._dataset.id}) is clean")

        else:
            logger.debug(f"Installing dataset {self.uri} to {self._datadir}")
            try:
                self._dataset: dl.Dataset = dl.clone(  # type: ignore
                    self.uri, self._datadir, result_renderer="disabled"
                )
            except IncompleteResultsError as e:
                raise_error(f"Failed to clone dataset: {e.failed}")
            logger.debug("Dataset installed")
        self._was_cloned = not isinstalled

        self.datalad_commit_id = self._dataset.repo.get_hexsha(  # type: ignore
            self._dataset.repo.get_corresponding_branch()  # type: ignore
        )
        self.datalad_id = self._dataset.id

    def cleanup(self) -> None:
        """Cleanup the datalad dataset."""
        if self._was_cloned:
            logger.debug("Removing dataset with reckless='kill'")
            self._dataset.remove(reckless="kill", result_renderer="disabled")
        else:
            logger.debug("Dropping files that were downloaded")
            for f in self._got_files:
                logger.debug(f"Dropping {f}")
                self._dataset.drop(f, result_renderer="disabled")

    def __getitem__(self, element: Element) -> dict:
        """Implement single element indexing in the Datalad database.

        It will first obtain the paths from the parent class and then
        ``datalad get`` each of the files.

        Parameters
        ----------
        element : str or tuple of str
            The element to be indexed. If one string is provided, it is
            assumed to be a tuple with only one item. If a tuple is provided,
            each item in the tuple is the value for the replacement string
            specified in ``"replacements"``.

        Returns
        -------
        dict
            Dictionary of paths for each type of data required for the
            specified element.

        """
        out = super().__getitem__(element)
        out = self._dataset_get(out)
        return out

    def __enter__(self) -> "DataladDataGrabber":
        """Implement context entry."""
        self.install()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        """Implement context exit."""
        logger.debug("Cleaning up dataset")
        self.cleanup()
        logger.debug("Dataset state restored")
