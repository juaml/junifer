from scipy.stats import zscore
"""Provide class for root sum of squares of edgewise timeseries."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
#          Nicolás Nieto <n.nieto@fz-juelich.de>
#          Sami Hamdan <s.hamdan@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Dict, List

import numpy as np
from nilearn.maskers import NiftiLabelsMasker

from ..data import load_atlas
from ..utils import logger
from .base import BaseMarker


class RSSETSMarker(BaseMarker):
    """Class for root sum of squares of edgewise timeseries.

    Parameters
    ----------
    atlas : str
        The name of the atlas.
    aggregation_method : str, optional
        The aggregation method (default "mean").

    """

    def __init__(self, atlas: str, aggregation_method: str = "mean") -> None:
        """Initialize the class."""
        self.atlas = atlas
        on = ["BOLD"]
        super().__init__(on=on)

    def get_output_kind(self, input: List[str]) -> List[str]:
        """Get output kind.

        Parameters
        ----------
        input : list of str
            The input to the marker. The list must contain the
            available Junifer Data dictionary keys.

        Returns
        -------
        list of str
            The updated list of output kinds, as storage possibilities.

        """
        outputs = []
        for t_input in input:
            if input in ["BOLD"]:
                outputs.append("timeseries")
            else:
                raise ValueError(f"Unknown input kind for {t_input}")
        return outputs

    # TODO: complete type annotations
    def store(self, kind: str, out, storage) -> None:
        """Store.

        Parameters
        ----------
        kind
        out
        storage

        """
        logger.debug(f"Storing {kind} in {storage}")
        if kind in ["BOLD"]:
            storage.store_timeseries(**out)

    def compute(self, input: Dict) -> Dict:
        """Compute.

        Take a timeseries of brain areas, and calculate timeseries for each
        edge according to the method outlined in [1]_. For more information,
        check https://github.com/brain-networks/edge-ts/blob/master/main.m

        Parameters
        ----------
        input : dict of the BOLD data

        Returns
        -------
        dict
            The computed result as dictionary. The key "RSS" contains the root
            sum of squares of the edge-wise time series.

        References
        ----------
        .. [1] Zamani Esfahlani et al. (2020)
               High-amplitude cofluctuations in cortical activity drive
               functional connectivity
               doi: 10.1073/pnas.2005531117

        """
        # indices of unique edges (lower triangle)
        u, v = np.tril_indices(n_roi, k=-1)

        ets = timeseries[:, u] * timeseries[:, v]
        out["RSS"] = np.sum(ets**2, 1) ** 0.5

        return out
