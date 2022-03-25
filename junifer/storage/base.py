# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
import numpy as np
import pandas as pd
import json
import hashlib
from abc import ABC, abstractmethod

from ..utils import logger
from .. import __version__


def process_meta(meta):
    """Process the metadata for storage. It removes the "element" key
    and adds the "_element_keys" with the keys used to index the element.

    Parameters
    ----------
    meta: dict
        The metadata. Must contain the key 'element'
    return_idx: bool
        If true, return the pandas index to be stored. Defaults to false
    n_rows: int
        Number of rows to create (if return_idx is true)
    rows_col_name: str
        The column name to use in case n_rows > 1. If None (default) and
        n_rows > 1, the name will be 'index'.

    Returns
    -------
    md5_hash: str
        The md5 hash of the meta
    meta : dict
        The metadata processed for storage
    idx : pd.MultiIndex
        The pandas index (if return_idx is True)
    """
    if meta is None:
        raise ValueError('Meta must be a dict (currently is None)')
    t_meta = meta.copy()
    element = t_meta.pop('element', None)
    if element is None:
        if '_element_keys' not in t_meta:
            raise ValueError(
                'Meta must contain the key "element" or "_element_keys"')
    else:
        if isinstance(element, dict):
            t_meta['_element_keys'] = list(element.keys())
        else:
            t_meta['_element_keys'] = ['element']
    md5_hash = _meta_hash(t_meta)
    return md5_hash, t_meta


def _meta_hash(meta):
    """Compute the md5 hash of the meta

    Parameters
    ----------
    meta: dict
        The metadata. Must contain the key 'element'

    Returns
    -------
    md5: str
        The md5 hash of the meta
    """
    logger.debug(f'Hashing meta {meta}')
    meta_md5 = hashlib.md5(
        json.dumps(meta, sort_keys=True).encode('utf-8')).hexdigest()
    logger.debug(f'Hash computed: {meta_md5}')
    return meta_md5


def element_to_index(meta, n_rows=1, rows_col_name=None):
    """Convert the element meta to index

    Parameters
    ----------
    meta: dict
        The metadata. Must contain the key 'element'
    n_rows: int
        Number of rows to create. Defaults to 1.
    rows_col_name: str
        The column name to use in case n_rows > 1. If None (default) and
        n_rows > 1, the name will be 'index'.

    Returns
    -------
    index: pd.MultiIndex
        The index of the dataframe to store

    Raises
    ------
    ValueError
        If the meta does not contain the key 'element'
    """
    if 'element' not in meta:
        raise ValueError(
            'To create and index, meta must contain the key "element"')
    element = meta['element']
    if not isinstance(element, dict):
        element = dict(element=element)
    if rows_col_name is None:
        rows_col_name = 'idx'
    elem_idx = {
        k: [v] * n_rows for k, v in element.items()
    }
    elem_idx[rows_col_name] = np.arange(n_rows)  # type: ignore
    index = pd.MultiIndex.from_frame(
        pd.DataFrame(elem_idx, index=range(n_rows)))
    return index


def element_to_prefix(element):
    logger.debug(f'Converting element {element} to prefix')
    prefix = 'element'
    if isinstance(element, tuple):
        prefix = f"{prefix}_{'_'.join([f'{x}' for x in element])}"
    elif isinstance(element, dict):
        prefix = f"{prefix}_{'_'.join([f'{x}' for x in element.values()])}"
    elif isinstance(element, (str, int)):
        prefix = f'{prefix}_{element}'
    else:
        raise ValueError(f'Cannot convert element {element} to prefix. '
                         'Must be a str, tuple or dict')
    logger.debug(f'Converted prefix {prefix}')
    return f'{prefix}_'


class BaseFeatureStorage(ABC):
    """
    Base class for feature storage.
    """

    def __init__(self, uri, single_output=False):
        self.uri = uri
        self.single_output = single_output

    def get_meta(self):
        meta = {}
        meta['versions'] = {
            'junifer': __version__,
        }
        return meta

    @abstractmethod
    def validate(self, input):
        """Validate the input to the pipeline step.

        Parameters
        ----------
        input : Junifer Data dictionary
            The input to the pipeline step.

        Raises
        ------
        ValueError:
            If the input does not have the required data.
        """
        raise NotImplementedError('validate_input not implemented')

    @abstractmethod
    def list_features(self, return_df=False):
        """List the features in the storage
        Parameters
        ----------
            return_df : bool
            If True, return a dataframe. If False, (default) return a
            dictionary
        Returns
        -------
        features: dict(str, dict) | pd.DataFrame
            List of features in the storage. If dictionarly, the keys are the
            feature names to be used in read_features. The values are the
            metadata of each feature.
        """
        raise NotImplementedError('list_features not implemented')

    @abstractmethod
    def read_df(self, feature_name=None, feature_md5=None):
        """Read the features from the storage

        Returns
        -------
        out: pd.DataFrame
            The features as a dataframe
        """
        raise NotImplementedError('read_df not implemented')

    @abstractmethod
    def store_metadata(self, meta):
        raise NotImplementedError('store_metadata not implemented')

    @abstractmethod
    def store_matrix2d(self, data, meta, col_names=None, row_names=None):
        raise NotImplementedError('store_matrix2d not implemented')

    @abstractmethod
    def store_table(self, data, meta, columns=None, rows_col_name=None):
        raise NotImplementedError('store_table not implemented')

    @abstractmethod
    def store_df(self, df, meta):
        raise NotImplementedError('store_df not implemented')

    @abstractmethod
    def store_timeseries(self, data, meta):
        raise NotImplementedError('store_timeseries not implemented')

    @abstractmethod
    def collect(self):
        raise NotImplementedError('collect not implemented')


class PandasFeatureStoreage(BaseFeatureStorage):

    def _meta_row(self, meta, meta_md5):
        """Convert the meta to a dataframe row"""
        data_df = {}
        for k, v in meta.items():
            data_df[k] = json.dumps(v, sort_keys=True)
        if 'marker' in meta:
            data_df['name'] = meta['marker']['name']
        df = pd.DataFrame(data_df, index=[meta_md5])
        df.index.name = 'meta_md5'
        return df
