# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL
from pathlib import Path
import tempfile

import datalad.api as dl
from abc import ABC, abstractmethod

from ..api.decorators import register_datagrabber
from ..utils.logging import logger, raise_error


def _validate_types(types):
    """
    Validate the types
    """
    if not isinstance(types, list):
        raise_error("types must be a list", TypeError)
    if any(not isinstance(x, str) for x in types):
        raise_error("types must be a list of strings", TypeError)


def _validate_patterns(types, patterns):
    """
    Validate the patterns.
    """
    _validate_types(types)
    if not isinstance(patterns, dict):
        raise_error("patterns must be a dict", TypeError)
    if len(types) != len(patterns):
        raise_error("types and patterns must have the same length", ValueError)

    if any(x not in patterns for x in types):
        raise_error("patterns must contain all types", ValueError)


class BaseDataGrabber(ABC):
    """Base DataGrabber class (abstract).

    Attributes
    ----------
    datadir
    types : list
        List of data types to be grabbed.

    Methods
    -------
    get_elements : List
        Returns a list of elements that can be grabbed. The elements can be
        strings, tuples or any object that will be then used as a key to
        index the datagrabber
    __getitem__(element) : dict[str -> Path]
        Returns a dictionary of paths for each type of data required for the
        specified element. Use the element as a key to index the datagrabber.
    __enter__() : self
        Returns the object itself. Can be overridden by subclasses.
    __exit__() : None
        Does nothing. Can be overridden by subclasses to clean up after
        `__enter__`
    """
    def __init__(self, types, datadir):
        """Initialize a BaseDataGrabber object.

        Parameters
        ----------
        types : list of str
            The types of data to be grabbed.
        datadir : str or Path
            That directory where the data is/will be stored.
        """
        _validate_types(types)
        if not isinstance(datadir, Path):
            datadir = Path(datadir)
        self._datadir = datadir
        self.types = types

    @property
    def datadir(self):
        """
        Returns
        -------
        Path to the data directory. Implemented as a property, can be
        overridden by subclasses.
        """
        return self._datadir

    def __iter__(self):
        """Iterate over elements in the datagrabber.

        Yields
        ------
        element : object
            An element that can be indexed by the datagrabber.
        """
        for elem in self.get_elements():
            yield elem

    @abstractmethod
    def __getitem__(self, element):
        raise NotImplementedError('__getitem__ not implemented')

    @abstractmethod
    def get_elements(self):
        raise NotImplementedError('get_elements not implemented')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        pass


@register_datagrabber
class BIDSDataGrabber(BaseDataGrabber):
    """BIDS DataGrabber class. Implements a DataGrabber that understands BIDS
    database format.

    Attributes
    ----------
    datadir
    types : list
        List of data types to be grabbed.
    patterns : dict[str -> str]
        Patterns for each type of data.

    Methods
    -------
    get_elements: list[str]
        Returns a list of elements that can be grabbed. Each element is a
        subject in the BIDS database.
    __getitem__(str): dict[str -> Path]
        Returns a dictionary of paths for each type of data required for the
        specified element. Each occurrence of the string `{subject}` is
        replaced by the indexed element
    """
    def __init__(self, types=None, patterns=None, **kwargs):
        """Initialize a BaseDataGrabber object.

        Parameters
        ----------
        types : list of str
            The types of data to be grabbed.
        patterns : dict[str -> str]
            Patterns for each type of data. The keys are the types and the
            values are the patterns. Each occurrence of the string `{subject}`
            in the pattern will be replaced by the indexed element.
        datadir : str or Path
            That directory where the data is/will be stored.
        """
        _validate_patterns(types, patterns)
        super().__init__(types=types, **kwargs)
        self.patterns = patterns

    def get_elements(self):
        """Get all the elements in the BIDS database

        Returns
        -------
        elems : list[str]
            List of all the elements in the database root directory
        """
        elems = [x.name for x in self.datadir.iterdir() if x.is_dir()]
        return elems

    def __getitem__(self, element):
        """Index one element in the BIDS database.

        Each occurrence of the string `{subject}` is replaced by the indexed
        element.

        Parameters
        ----------
        element : str
            The element to be indexed.
        Returns
        -------
        out : dict[str -> Path]
            Dictionary of paths for each type of data required for the
            specified element.
        """
        out = {}
        for t_type in self.types:
            t_pattern = self.patterns[t_type]  # type: ignore
            t_replace = t_pattern.replace('{subject}', element)
            t_out = self.datadir / element / t_replace
            out[t_type] = t_out

        return out


@register_datagrabber
class DataladDataGrabber(BaseDataGrabber):
    """
    Datalad DataGrabber class. Implements a DataGrabber that gets data from
    a datalad sibling.

    Attributes
    ----------
    datadir
    uri : str
        URI of the datalad sibling.

    Methods
    -------
    install:
        Installs (clones) the datalad dataset into the datadir. This method
        is called automatically when the datagrabber is used within a `with`
        statement.
    remove:
        Remove the datalad dataset from the datadir. This method is called
        automatically when the datagrabber is used within a `with` statement.

    Note
    ----
    By itself, this class is still abstract as the `__getitem__` method relies
    on the parent class `BaseDataGrabber.__getitem__` which is not yet
    implemented. This class is intended to be used as a superclass of a class
    with multiple inheritance. See :class:`BIDSDataladDataGrabber` for a
    concrete class implementation.

    """
    def __init__(self, rootdir='.', datadir=None, uri=None, **kwargs):
        """Initialize a DataladDataGrabber object.

        Parameters
        ----------
        rootdir : str or Path
            The path within the datalad dataset to the root directory.
        datadir : str or Path
            That directory where the datalad dataset will be cloned. If None,
            (default), the datalad dataset will be cloned into a temporary
            directory.
        uri : str
            URI of the datalad sibling.
        """
        if uri is None:
            raise_error('uri must be provided', ValueError)
        if datadir is None:
            logger.warning('datadir is None, creating a temporary directory')
            datadir = tempfile.mkdtemp()
            logger.info(f'datadir set to {datadir}')
        super().__init__(datadir=datadir, **kwargs)
        self.uri = uri
        self._rootdir = rootdir

    def __enter__(self):
        self.install()
        return self

    @property
    def datadir(self):
        return super().datadir / self._rootdir

    def install(self):
        """Install the datalad dataset into the datadir."""
        self.dataset = dl.install(  # type: ignore
            self._datadir, source=self.uri)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.remove()

    def remove(self):
        """Remove the datalad dataset from the datadir."""
        self.dataset.remove(recursive=True)

    def _dataset_get(self, out):
        for _, v in out.items():
            self.dataset.get(v)

    def __getitem__(self, element):
        """Index one element in the Datalad database. It will first obtain
        the paths from the parent class and then `datalad get` each of the
        files."""
        out = super().__getitem__(element)
        self._dataset_get(out)
        return out


class BIDSDataladDataGrabber(DataladDataGrabber, BIDSDataGrabber):
    """BIDS Datalad DataGrabber class.
    Implements a DataGrabber that gets data from a datalad sibling which
    follows a BIDS format.

    See Also
    --------
    DataladDataGrabber
    BIDSDataGrabber

    """
    def __init__(self, types=None, patterns=None, **kwargs):
        _validate_patterns(types, patterns)
        super().__init__(types=types, patterns=patterns, **kwargs)
        self.patterns = patterns
