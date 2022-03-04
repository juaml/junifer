# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
import numpy as np
import pandas as pd

from .. import __version__


def _element_to_index(meta, n_rows=1, row_names=None):
    """Convert the element meta to index

    Parameters
    ----------
    meta: dict
        The metadata. Must contain the key 'element'
    n_rows: int
        Number of rows to create
    row_names: list
        The row names to use ins case n_rows > 1

    Returns
    -------
    index: pd.MultiIndex
        The index of the dataframe to store
    """
    element = meta['element']
    if not isinstance(element, dict):
        element = dict(element=element)
    if n_rows > 1:
        elem_idx = {
            k: v * n_rows for k, v in element.items()
        }
        elem_idx[row_names] = np.arange(n_rows)
    else:
        elem_idx = element
    index = pd.MultiIndex.from_frame(
        pd.DataFrame(elem_idx, index=range(n_rows)))

    return index


class BaseFeatureStorage():
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

    def store_matrix2d(self, data, col_names=None, row_names=None, meta=None):
        raise NotImplementedError('store_matrix2d not implemented')

    def store_table(self, data, columns=None, row_names=None, meta=None):
        raise NotImplementedError('store_table not implemented')

    def store_df(self, df):
        raise NotImplementedError('store_df not implemented')

    def store_timeseries(self, data):
        raise NotImplementedError('store_timeseries not implemented')
