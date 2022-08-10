"""Provide abstract base class for feature storage via pandas."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import json
from typing import Dict

import pandas as pd

from .base import BaseFeatureStorage


class PandasBaseFeatureStorage(BaseFeatureStorage):
    """Abstract base class for feature storage via pandas.

    For every interface that is required, one needs to provide a concrete
    implementation of this abstract class.

    See Also
    --------
    BaseFeatureStorage

    """

    def __init__(**kwargs) -> None:
        """Initialize the class."""
        super().__init__(**kwargs)

    def _meta_row(self, meta: Dict, meta_md5: str) -> pd.DataFrame:
        """Convert the metadata to a pandas DataFrame.

        Parameters
        ----------
        meta : dict
            The metadata as a dictionary.
        meta_md5 : str
            The MD5 hash of the metadata.

        Returns
        -------
        pandas.DataFrame

        """
        data_df = {}
        for k, v in meta.items():
            data_df[k] = json.dumps(v, sort_keys=True)
        if "marker" in meta:
            data_df["name"] = meta["marker"]["name"]
        df = pd.DataFrame(data_df, index=[meta_md5])
        df.index.name = "meta_md5"
        return df
