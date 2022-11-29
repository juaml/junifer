"""Provide abstract base class for datalad datagrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import tempfile
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

import datalad.api as dl
from datalad.support.gitrepo import GitRepo

from ..api.decorators import register_datagrabber
from ..utils import logger, raise_error, warn_with_log
from .base import BaseDataGrabber


@register_datagrabber
class DataladDataGrabber(BaseDataGrabber):
    """Abstract base class for data fetching via Datalad.

    Defines a Data Grabber that gets data from a datalad sibling.

    Parameters
    ----------
    rootdir : str or Path, optional
        The path within the datalad dataset to the root directory
        (default ".").
    datadir : str or Path, optional
        That directory where the datalad dataset will be cloned. If None,
        the datalad dataset will be cloned into a temporary directory
        (default None).
    uri : str, optional
        URI of the datalad sibling (default None).
    **kwargs
        Keyword arguments passed to superclass.

    Methods
    -------
    install:
        Installs (clones) the datalad dataset into the `datadir`. This method
        is called automatically when the datagrabber is used within a context.
    remove:
        Removes the datalad dataset from the `datadir`. This method is called
        automatically when the datagrabber is used within a context.

    See Also
    --------
    BaseDataGrabber
        For the abstract base class of any datagrabber.

    Notes
    -----
    By itself, this class is still abstract as the `__getitem__` method relies
    on the parent class `BaseDataGrabber.__getitem__` which is not yet
    implemented. This class is intended to be used as a superclass of a class
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
            logger.warning("`datadir` is None, creating a temporary directory")
            # Create temporary directory
            datadir = tempfile.mkdtemp()
            logger.info(f"`datadir` set to {datadir}")
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

    @property
    def datadir(self) -> Path:
        """Get data directory path."""
        return super().datadir / self._rootdir

    def _get_dataset_id_remote(self) -> str:
        """Get the dataset id from the remote.

        Returns
        -------
        str
            The dataset id.

        """
        remote_id = None
        with tempfile.TemporaryDirectory() as tmpdir:
            logger.debug(f"Querying {self.uri} for dataset ID")
            repo = GitRepo.clone(
                self.uri, path=tmpdir, clone_options=["-n", "--depth=1"]
            )
            repo.checkout(name=".datalad/config", options=["HEAD"])
            remote_id = repo.config.get("datalad.dataset.id", None)
            logger.debug(f"Got remote dataset ID = {remote_id}")
        if remote_id is None:
            raise_error("Could not get dataset ID from remote")
        return remote_id

    def _dataset_get(self, out: Dict) -> Dict:
        """Get the dataset found from the path in `out`.

        Parameters
        ----------
        out : dict
            The dictionary from which path need to be searched.

        Returns
        -------
        dict
            The modified dictionary with meta updated.

        """
        to_get = [v["path"] for v in out.values() if "path" in v]

        if len(to_get) > 0:
            logger.debug(f"Getting {len(to_get)} files using datalad:")
            for fname in to_get:
                logger.debug(f"\t: {fname}")

            dl_out = self._dataset.get(to_get, result_renderer="disabled")
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
        """Install the datalad dataset into the datadir.

        Raises
        ------
        ValueError
            If the dataset is already installed but with a different ID.
        """
        isinstalled = dl.Dataset(self._datadir).is_installed()
        if isinstalled:
            logger.debug("Dataset already installed")
            self._got_files = []
            self._dataset: dl.Dataset = dl.Dataset(self._datadir)

            remote_id = self._get_dataset_id_remote()
            if remote_id != self._dataset.id:
                raise_error(
                    "Dataset already installed but with a different "
                    f"ID: {self._dataset.id} (local) != {remote_id} (remote)"
                )

            # Check for dirty datasets:
            status = self._dataset.status()
            if any([x["state"] != "clean" for x in status]):
                self.datalad_dirty = True
                warn_with_log(
                    "At least one file is not clean, Junifer will "
                    "consider this dataset as dirty."
                )
            else:
                logger.debug("Dataset is clean")

        else:
            logger.debug(f"Installing dataset {self.uri} to {self._datadir}")
            self._dataset: dl.Dataset = dl.clone(  # type: ignore
                self.uri, self._datadir, result_renderer="disabled"
            )
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

    def __getitem__(self, element: Union[str, Tuple]) -> Dict:
        """Implement single element indexing in the Datalad database.

        It will first obtain the paths from the parent class and then
        `datalad get` each of the files.

        This method only works with multiple inheritance.

        Parameters
        ----------
        element : str or tuple
            The element to be indexed. If one string is provided, it is
            assumed to be a tuple with only one item. If a tuple is provided,
            each item in the tuple is the value for the replacement string
            specified in "replacements".

        Returns
        -------
        dict
            Dictionary of paths for each type of data required for the
            specified element.

        """
        out = super().__getitem__(element)
        out = self._dataset_get(out)
        return out

    def __enter__(self):
        """Implement context entry."""
        self.install()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Implement context exit."""
        logger.debug("Cleaning up dataset")
        self.cleanup()
        logger.debug("Dataset state restored")
