"""Provide class and functions for base datagrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL

from pathlib import Path
import re
import tempfile

import datalad.api as dl
from abc import ABC, abstractmethod

from ..api.decorators import register_datagrabber
from ..utils.logging import logger, raise_error, warn


def _validate_types(types):
    """Validate the types."""
    if not isinstance(types, list):
        raise_error("types must be a list", TypeError)  # type: ignore
    if any(not isinstance(x, str) for x in types):
        raise_error(
            "types must be a list of strings", TypeError)  # type: ignore


def _validate_replacements(replacements, patterns):
    """Validate the replacements."""
    if not isinstance(replacements, list):
        raise_error("replacements must be a list", TypeError)  # type: ignore
    if any(not isinstance(x, str) for x in replacements):
        raise_error(
            "replacements must be a list of strings",
            TypeError)  # type: ignore

    for x in replacements:
        if all(x not in y for y in patterns.values()):
            warn(f"Replacement {x} is not part of any pattern")


def _validate_patterns(types, patterns):
    """Validate the patterns."""
    _validate_types(types)
    if not isinstance(patterns, dict):
        raise_error("patterns must be a dict", TypeError)  # type: ignore
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
        logger.debug('Initializing BaseDataGrabber')
        logger.debug(f'\t_datadir = {datadir}')
        logger.debug(f'\ttypes = {types}')
        self._datadir = datadir
        self.types = types

    def get_types(self):
        """Get types."""
        return self.types.copy()

    def get_meta(self):
        """Get metadata."""
        t_meta = {}
        t_meta['class'] = self.__class__.__name__
        for k, v in vars(self).items():
            if not k.startswith('_'):
                t_meta[k] = v
        return t_meta

    def get_element_keys(self):
        """Get element keys."""
        return 'element'

    @property
    def datadir(self):
        """Get data directory path.

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

    def __getitem__(self, element):
        """Get item implementation."""
        logger.info(f'Getting element {element}')
        out = {}
        out['meta'] = dict(datagrabber=self.get_meta())
        return out

    @abstractmethod
    def get_elements(self):
        """Get elements."""
        raise_error(
            'get_elements not implemented',
            NotImplementedError)  # type: ignore

    def __enter__(self):
        """Context entry implementation."""
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Context exit implementation."""
        pass


@register_datagrabber
class PatternDataGrabber(BaseDataGrabber):
    """Pattern DataGrabber class (abstract).

    Implements a DataGrabber that understands patterns to grab data.

    Attributes
    ----------
    datadir: Path
        Directory where the data is stored
    types : list[str]
        List of data types to be grabbed.
    patterns : dict[str -> str]
        Patterns for each type of data.
    replacements: list[str]
        Replacements in the patterns for each item in the `element` tuple.

    Methods
    -------
    get_elements: list[str]
        Returns a list of elements that can be grabbed. Each element is a
        subject in the BIDS database.
    __getitem__(str): dict[str -> dict]
        Returns a dictionary of paths for each type of data required for the
        specified element. Each occurrence of the string `{subject}` is
        replaced by the indexed element
    """

    def __init__(self, types=None, patterns=None, replacements=None, **kwargs):
        """Initialize a BaseDataGrabber object.

        Parameters
        ----------
        types : list[str]
            The types of data to be grabbed.
        patterns : dict[str -> str]
            Patterns for each type of data. The keys are the types and the
            values are the patterns. Each occurrence of the string `{subject}`
            in the pattern will be replaced by the indexed element.
        datadir : str or Path
            That directory where the data is/will be stored.
        """
        _validate_patterns(types, patterns)
        if not isinstance(replacements, list):
            replacements = [replacements]
        _validate_replacements(replacements, patterns)
        super().__init__(types=types, **kwargs)
        logger.debug('Initializing PatternDataGrabber')
        logger.debug(f'\tpatterns = {patterns}')
        logger.debug(f'\treplacements = {replacements}')
        self.patterns = patterns
        self.replacements = replacements

    def _replace_patterns_regex(self, pattern):
        """Replace the patterns in the pattern with the named groups.

        It allows elements to be obtained from the filesystem.

        Parameters
        ----------
        pattern : str
            The pattern to be replaced.

        Returns
        -------
        re_pattern : str
            The regular expression with the named groups.
        glob_pattern : str
            The search pattern to be used with glob

        """
        re_pattern = pattern
        glob_pattern = pattern
        for t_r in self.replacements:
            # Replace the first of each with a named group definition
            re_pattern = re_pattern.replace(
                f'{{{t_r}}}', f'(?P<{t_r}>.*)', 1)

        for t_r in self.replacements:
            # Replace the second appearance of each with the named group
            # back reference
            re_pattern = re_pattern.replace(f'{{{t_r}}}', f'(?P={t_r})')

        for t_r in self.replacements:
            glob_pattern = glob_pattern.replace(f'{{{t_r}}}', '*')
        return re_pattern, glob_pattern

    def get_elements(self):
        """Get the list of elements in the dataset.

        It will use regex to search for `replacements` in the `patterns` and
        return the intersection of the results for each type. That is, build a
        list of elements that have all the required types.

        Returns
        -------
        elements : list
            The list of elements in the dataset.
        """
        elements = None
        for t_type in self.types:
            types_element = set()
            t_pattern = self.patterns[t_type]  # get the pattern
            re_pattern, glob_pattern = self._replace_patterns_regex(t_pattern)
            for fname in self.datadir.glob(glob_pattern):
                suffix = fname.relative_to(self.datadir).as_posix()
                m = re.match(re_pattern, suffix)
                if m is not None:
                    t_element = tuple(m.group(k) for k in self.replacements)
                    if len(self.replacements) == 1:
                        t_element = t_element[0]
                    types_element.add(t_element)
            if elements is None:
                elements = types_element
            else:
                elements = elements.intersection(types_element)

        return list(elements)

    def _replace_patterns_glob(self, element, pattern):
        """Replace patterns with the element so it can be globbed.

        Parameters
        ----------
        element : tuple
            The element to be used in the replacement.
        pattern : str
            The pattern to be replaced.

        Returns
        -------
        str
            The pattern with the element replaced.
        """
        if len(element) != len(self.replacements):
            raise_error(
                f'The element length must be {len(self.replacements)}, '
                f'indicating {self.replacements}')
        to_replace = dict(zip(self.replacements, element))
        return pattern.format(**to_replace)

    def __getitem__(self, element):
        """Index one element in the database.

        Each occurrence of the strings in `replacements` is replaced by the
        corresponding item in the element tuple.

        Parameters
        ----------
        element : str or tuple
            The element to be indexed. If one string is provided, it is
            assumed to be a tuple with only one item. If a tuple is provided,
            each item in the tuple is the value for the replacement string
            specified in `replacements`.

        Returns
        -------
        out : dict[str -> Path]
            Dictionary of paths for each type of data required for the
            specified element.
        """
        out = super().__getitem__(element)
        if not isinstance(element, tuple):
            element = (element,)
        for t_type in self.types:
            t_pattern = self.patterns[t_type]  # type: ignore
            t_replace = self._replace_patterns_glob(element, t_pattern)
            if '*' in t_replace:
                t_matches = list(self.datadir.glob(t_replace))
                if len(t_matches) > 1:
                    raise_error(
                        f'More than one file matches for {element} / {t_type}:'
                        f' {t_matches}')
                elif len(t_matches) == 0:
                    raise_error(f'No file matches for {element} / {t_type}')
                t_out = t_matches[0]
            else:
                t_out = self.datadir / t_replace
            out[t_type] = dict(path=t_out)
        # Meta here is element and types
        out['meta']['element'] = dict(zip(self.replacements, element))
        return out


@register_datagrabber
class DataladDataGrabber(BaseDataGrabber):
    """Datalad DataGrabber class (abstract).

    Implements a DataGrabber that gets data from a datalad sibling.

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

    Notes
    -----
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
        logger.debug('Initializing DataladDataGrabber')
        logger.debug(f'\turi = {uri}')
        logger.debug(f'\t_rootdir = {rootdir}')
        self.uri = uri
        self._rootdir = rootdir

    def __enter__(self):
        """Context entry implementation."""
        self.install()
        return self

    @property
    def datadir(self):
        """Get data directory path."""
        return super().datadir / self._rootdir

    def install(self):
        """Install the datalad dataset into the datadir."""
        logger.debug(f'Installing dataset {self.uri} to {self._datadir}')
        self._dataset = dl.install(  # type: ignore
            self._datadir, source=self.uri)
        logger.debug('Dataset installed')

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Context exit implementation."""
        logger.debug('Removing dataset')
        self.remove()
        logger.debug('Dataset removed')

    def remove(self):
        """Remove the datalad dataset from the datadir."""
        self._dataset.remove(recursive=True)

    def _dataset_get(self, out):
        for _, v in out.items():
            if 'path' in v:
                logger.debug(f'Getting {v["path"]}')
                self._dataset.get(v['path'])
                logger.debug('Get done')

        # append the version of the dataset
        out['meta']['datagrabber']['dataset_commit_id'] = \
            self._dataset.repo.get_hexsha(
                self._dataset.repo.get_corresponding_branch())
        return out

    def __getitem__(self, element):
        """Index one element in the Datalad database.

        It will first obtain the paths from the parent class and then
        `datalad get` each of the files.

        This method only works with multiple inheritance.

        """
        out = super().__getitem__(element)
        out = self._dataset_get(out)
        return out


@register_datagrabber
class PatternDataladDataGrabber(DataladDataGrabber, PatternDataGrabber):
    """Pattern-based Datalad DataGrabber class (abstract).

    Implements a DataGrabber that gets data from a datalad sibling,
    interpreting patterns.


    See Also
    --------
    DataladDataGrabber
    PatternDataGrabber

    """

    def __init__(self, types=None, patterns=None, **kwargs):
        """Initialize the class."""
        _validate_patterns(types, patterns)
        super().__init__(types=types, patterns=patterns, **kwargs)
        self.patterns = patterns
