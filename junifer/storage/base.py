# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
import numpy as np
import pandas as pd
import json
import hashlib
from abc import ABC, abstractmethod

from .. import __version__


def meta_hash(meta):
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
    if meta is None:
        raise ValueError('Meta must be a dict (currently is None)')
    t_meta = meta.copy()
    meta_md5 = hashlib.md5(
        json.dumps(t_meta, sort_keys=True).encode('utf-8')).hexdigest()
    return meta_md5


def element_to_index(meta, n_rows=1, rows_col_name=None):
    """Convert the element meta to index

    Parameters
    ----------
    meta: dict
        The metadata. Must contain the key 'element'
    n_rows: int
        Number of rows to create
    rows_col_name: str
        The column name to use in case n_rows > 1. If None (default) and
        n_rows > 1, the name will be 'index'.

    Returns
    -------
    index: pd.MultiIndex
        The index of the dataframe to store
    """
    element = meta['element']
    if not isinstance(element, dict):
        element = dict(element=element)
    if n_rows > 1:
        if rows_col_name is None:
            rows_col_name = 'index'
        elem_idx = {
            k: [v] * n_rows for k, v in element.items()
        }
        elem_idx[rows_col_name] = np.arange(n_rows)
    else:
        elem_idx = element
    index = pd.MultiIndex.from_frame(
        pd.DataFrame(elem_idx, index=range(n_rows)))

    return index


class BaseFeatureStorage(ABC):
    """
    Base class for feature storage.
    """

    def __init__(self, uri):
        self.uri = uri

    def get_meta(self):
        meta = {}
        meta['versions'] = {
            'junifer': __version__,
        }
        return meta

    @abstractmethod
    def store_metadata(self, meta):
        raise NotImplementedError('store_metadata not implemented')

    @abstractmethod
    def store_matrix2d(self, data, col_names=None, row_names=None, meta=None):
        raise NotImplementedError('store_matrix2d not implemented')

    @abstractmethod
    def store_table(self, data, columns=None, row_names=None, meta=None):
        raise NotImplementedError('store_table not implemented')

    @abstractmethod
    def store_df(self, df):
        raise NotImplementedError('store_df not implemented')

    @abstractmethod
    def store_timeseries(self, data):
        raise NotImplementedError('store_timeseries not implemented')


class PandasFeatureStoreage(BaseFeatureStorage):

    def _meta_row(self, meta, meta_md5):
        """Converta the meta to a dataframe row"""
        data_df = {}
        for k, v in meta:
            data_df[k] = json.dumps(v, sort_keys=True)
        data_df['name'] = meta['marker']['name']
        df = pd.DataFrame(data_df, index=[meta_md5])
        return df
