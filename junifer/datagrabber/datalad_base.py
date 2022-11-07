"""Provide abstract base class for datalad datagrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import tempfile
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

import datalad.api as dl

from ..api.decorators import register_datagrabber
from ..utils import logger
from .base import BaseDataGrabber
from .utils import raise_error


@register_datagrabber
class DataladDataGrabber(BaseDataGrabber):
    """Abstract base class for data fetching via Datalad.

    Defines a DataGrabber that gets data from a datalad sibling.

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

    @property
    def datadir(self) -> Path:
        """Get data directory path."""
        return super().datadir / self._rootdir

    def _dataset_get(self, out: Dict) -> Dict:
        """Get the dataset found from the path in `out`.

        Parameters
        ----------
        out : dict
            The dictionary from which path need to be searched.

        Returns
        -------
        dict
            The modified dictionary with version appended.

        """
        dirty_status = False
        for _, v in out.items():
            if "path" in v:
                logger.debug(f"Getting {v['path']}")
                # Note, that `self._dataset.get` without an option would get
                # the content of all files in a (sub-dataset) if `v["path"]`
                # was to point to a subdataset rather than a file. This may be
                # a source of confusion (+ performance/storage issue) when
                # implementing a grabber.
                dl_out = self._dataset.get(v["path"])
                if not self._was_cloned:
                    # If the dataset was already installed, check that the
                    # file was actually downloaded to avoid removing a
                    # file that was already there.
                    if len(dl_out) > 1:
                        raise_error("More than one file downloaded. WTF?")
                    dl_out = dl_out[0]
                    if dl_out["status"] == "ok":
                        logger.debug("File downloaded")
                        self._got_files.append(v["path"])
                    elif dl_out["status"] == "notneeded":
                        dirty_status = True
                        logger.debug("File was already present")
                    else:
                        raise_error(f"File download failed: {dl_out}")
                logger.debug("Get done")

        assert self._dataset.repo is not None  # avoid errors from mypy

        # append the version of the dataset
        out["meta"]["datagrabber"][
            "dataset_commit_id"
        ] = self._dataset.repo.get_hexsha(
            self._dataset.repo.get_corresponding_branch()
        )

        # Set a flag to indicate that the dataset was dirty
        out["meta"]["datagrabber"]["dataset_dirty"] = dirty_status
        return out

    def install(self) -> None:
        """Install the datalad dataset into the datadir."""
        isinstalled = dl.Dataset(self._datadir).is_installed()
        if isinstalled:
            logger.debug("Dataset already installed")
            self._got_files = []
            self._dataset: dl.Dataset = dl.Dataset(self._datadir)
            # TODO: Check URI
        else:
            logger.debug(f"Installing dataset {self.uri} to {self._datadir}")
            self._dataset: dl.Dataset = \
                dl.clone(self.uri, self._datadir)  # type: ignore
            logger.debug("Dataset installed")
        self._was_cloned = not isinstalled

    def remove(self):
        """Remove the datalad dataset from the datadir."""
        if self._was_cloned:
            self._dataset.remove(recursive=True, reckless="kill")
        else:
            for f in self._got_files:
                self._dataset.drop(f)

    def __getitem__(self, element: Union[str, Tuple]) -> Dict[str, Path]:
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
        logger.debug("Removing dataset")
        self.remove()
        logger.debug("Dataset removed")
