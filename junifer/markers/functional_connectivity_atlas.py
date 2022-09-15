"""Provide base class for markers."""

# Authors: Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Kaustubh R. Patil <k.patil@fz-juelich.de>
# License: AGPL

from typing import Dict, List, Optional

from nilearn.connectome import ConnectivityMeasure
from sklearn.covariance import EmpiricalCovariance

from ..api.decorators import register_marker
from ..utils import logger
from .base import BaseMarker
from .parcel import ParcelAggregation


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
        self,
        atlas,
        agg_method="mean",
        agg_method_params=None,
        cor_method="covariance",
        cor_method_params=None,
        name=None,
    ) -> None:
        """Initialize the class."""
        self.atlas = atlas
        self.agg_method = agg_method
        self.agg_method_params = (
            {} if agg_method_params is None else agg_method_params
        )
        self.cor_method = cor_method
        self.cor_method_params = (
            {} if cor_method_params is None else cor_method_params
        )
        on = ["BOLD"]
        # default to nilearn behavior
        self.cor_method_params["empirical"] = self.cor_method_params.get(
            "empirical", False
        )

        super().__init__(on=on, name=name)

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
        outputs = ["matrix"]
        return outputs

    def compute(self, input: Dict, extra_input: Optional[Dict] = None) -> Dict:
        """Compute.

        Parameters
        ----------
        input : Dict[str, Dict]
            A single input from the pipeline data object in which to compute
            the marker.
        extra_input : Dict, optional
            The other fields in the pipeline data object. Useful for accessing
            other data kind that needs to be used in the computation. For
            example, the functional connectivity markers can make use of the
            confounds if available.

        Returns
        -------
        dict
            The computed result as dictionary. The following data will be
            included in the dictionary:
            - 'data': FC matrix as a 2D numpy array.
            - 'row_names': Row names as a list.
            - 'col_names': Col names as a list.
            - 'kind': The kind of matrix (tril, triu or full)
        """
        pa = ParcelAggregation(
            atlas=self.atlas,
            method=self.agg_method,
            method_params=self.agg_method_params,
            on="BOLD",
        )
        # get the 2D timeseries after parcel aggregation
        ts = pa.compute(input)

        if self.cor_method_params["empirical"]:
            cm = ConnectivityMeasure(
                cov_estimator=EmpiricalCovariance(),  # type: ignore
                kind=self.cor_method
            )
        else:
            cm = ConnectivityMeasure(kind=self.cor_method)
        out = {}
        out["data"] = cm.fit_transform([ts["data"]])[0]
        # create column names
        out["row_names"] = ts["columns"]
        out["col_names"] = ts["columns"]
        out["kind"] = "tril"
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
        storage.store_matrix2d(**out)
