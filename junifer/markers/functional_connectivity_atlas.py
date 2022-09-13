"""Provide base class for markers."""

# Authors: Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Kaustubh R. Patil <k.patil@fz-juelich.de>
# License: AGPL

from typing import Dict, List
from nilearn.connectome import ConnectivityMeasure
import numpy as np

from ..api.decorators import register_marker
from ..utils import logger, raise_error
from .base import BaseMarker, ParcelAggregation


@register_marker
class FunctionalConnectivityAtlas(BaseMarker):
    """Class for functional connectivity.

     Parameters
    ----------
    atlas
    agg_method
    agg_method_params
    cor_method
    cor_method_params
    name

    """

    def __init__(
        self, atlas, agg_method='mean', agg_method_params=None,
        cor_method='cov', cor_method_params=None, name=None
    ) -> None:
        """Initialize the class."""
        self.atlas = atlas
        self.agg_method = agg_method
        self.agg_method_params = {} if agg_method_params is None \
            else agg_method_params
        self.cor_method = cor_method
        self.cor_method_params = {} if cor_method_params is None \
            else cor_method_params
        on = ["BOLD"]
        super().__init__(on=on, name=name)

    def get_meta(self, kind: str) -> Dict:
        """Get metadata.

        Parameters
        ----------
        kind : str
            The kind of pipeline step.

        Returns
        -------
        dict
            The metadata as a dictionary.

        """
        s_meta = super().get_meta()
        # same marker can be "fit"ted into different kinds, so the name
        # is created from the kind and the name of the marker
        s_meta["name"] = f"{kind}_{self.name}"
        s_meta["kind"] = kind
        return {"marker": s_meta}

    def validate_input(self, input: List[str]) -> None:
        """Validate input.

        Parameters
        ----------
        input : list of str
            The input to the pipeline step. The list must contain the
            available Junifer Data dictionary keys.

        Raises
        ------
        ValueError
            If the input does not have the required data.

        """
        if not any(x in input for x in self._valid_inputs):
            raise_error(
                "Input does not have the required data."
                f"\t Input: {input}"
                f"\t Required (any of): {self._valid_inputs}"
            )

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
        outputs = ["table"]
        return outputs

    def compute(self, input: Dict) -> Dict:
        """Compute.

        Parameters
        ----------
        input : Dict[str, Dict]
            The input to the pipeline step. The list must contain the
            available Junifer Data dictionary keys.

        Returns
        -------
        1D numpy array
            The lower traingle of the FC matrix as a 1D numpy array.

        """
        pa = ParcelAggregation(atlas=self.atlas, method=self.agg_method,
                               method_params=self.agg_method_params,
                               on="BOLD")
        # get the 2D timeseries after parcel aggregation
        ts = pa.compute()
        cm = ConnectivityMeasure(kind=self.cor_method)
        out = cm.fit_transform(ts)
        out = out[np.tril_indices(3, k=-1)]
        return out

    # TODO: complete type annotations
    def store(self, kind: str, out: Dict, storage) -> None:
        """Store.

        Parameters
        ----------
        input
        out

        """
        logger.debug(f"Storing {kind} in {storage}")
        storage.store_table(**out)

