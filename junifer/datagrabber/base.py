from pathlib import Path
import tempfile

import datalad.api as dl

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
    if not isinstance(types, list):
        raise_error("types must be a list", TypeError)
    if not isinstance(patterns, dict):
        raise_error("patterns must be a dict", TypeError)
    if len(types) != len(patterns):
        raise ValueError("types and patterns must have the same length")
    for i in range(len(types)):
        if not isinstance(types[i], str):
            raise_error("types must be a list of strings", TypeError)

    if any(x not in patterns for x in types):
        raise_error("patterns must contain all types", TypeError)


class BaseDataGrabber:
    def __init__(self, types, datadir):
        _validate_types(types)
        if not isinstance(datadir, Path):
            datadir = Path(datadir)
        self._datadir = datadir
        self.types = types

    @property
    def datadir(self):
        return self._datadir

    def __iter__(self):
        for elem in self.get_elements():
            yield elem

    def __getitem__(self, element):
        raise NotImplementedError('__getitem__ not implemented')

    def get_elements(self):
        raise NotImplementedError('get_elements not implemented')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        pass


class BIDSDataGrabber(BaseDataGrabber):
    def __init__(self, types=None, patterns=None, **kwargs):
        _validate_patterns(types, patterns)
        super().__init__(types=types, **kwargs)
        self.patterns = patterns

    def get_elements(self):
        elems = [x.name for x in self.datadir.iterdir() if x.is_dir()]
        return elems

    def __getitem__(self, element):
        out = {}
        for t_type in self.types:
            t_pattern = self.patterns[t_type]  # type: ignore
            t_replace = t_pattern.replace('{subject}', element)
            t_out = self.datadir / element / t_replace
            out[t_type] = t_out

        return out


class DataladDataGrabber(BaseDataGrabber):
    def __init__(self, rootdir='.', datadir=None, uri=None, **kwargs):
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
        self.dataset = dl.install(  # type: ignore
            self._datadir, source=self.uri)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.remove()

    def remove(self):
        self.dataset.remove(recursive=True)

    def __getitem__(self, element):
        out = super().__getitem__(element)
        for _, v in out.items():
            self.dataset.get(v)
        return out


class BIDSDataladDataGrabber(DataladDataGrabber, BIDSDataGrabber):
    def __init__(self, types=None, patterns=None, **kwargs):
        _validate_patterns(types, patterns)
        super().__init__(types=types, patterns=patterns, **kwargs)
        self.patterns = patterns
