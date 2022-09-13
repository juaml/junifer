from scipy.stats import zscore
import numpy as np

from ..data import load_atlas
from ..utils import logger
from .base import BaseMarker


class RSSETSMarker(BaseMarker):
    def __init__(self, atlas):
        self.atlas = atlas
        on = ["BOLD"]
        super().__init__(self, on=on)

    def get_output_kind(self, input):
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

    def compute(self, input):
        """ This function will take a timeseries of brain areas, and calculate
        timeseries for each edge according to the method outlined by
        Zamani Esfahlani et al. (2020) --
        (https://www.pnas.org/content/117/45/28393#sec-21). For their
        code see https://github.com/brain-networks/edge-ts/blob/master/main.m

        Parameters
        ----------
        timeseries : np.array
            number of rows should correspond to number of time frames
            (first dimension), number of columns should correspond to number of
            nodes (second dimension)

        Returns
        -------
        ets : tuple (np.array, np.array)
                Edge-timeseries with rows corresponding to time points and columns
                corresponding to unique edges
        """
        niimg = input["data"]

        t_atlas, _, _ = load_atlas(self.atlas, resolution=resolution) 
        masker = NiftiLabelsMasker(t_atlas)
        timeseries = zscore(masker.fit_transform(niimg))

        _, n_roi = timeseries.shape

        # indices of unique edges (lower triangle)
        u, v = np.tril_indices(n_roi, k=-1)

        ets = timeseries[:, u] * timeseries[:, v]
        return np.sum(ets**2, 1) ** 0.5
