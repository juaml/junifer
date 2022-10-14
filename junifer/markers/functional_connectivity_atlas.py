"""Provide class for functional connectivity."""

# Authors: Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Kaustubh R. Patil <k.patil@fz-juelich.de>
# License: AGPL

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from nilearn.connectome import ConnectivityMeasure
from sklearn.covariance import EmpiricalCovariance

from ..api.decorators import register_marker
from ..utils import logger
from .base import BaseMarker
from .parcel import ParcelAggregation


if TYPE_CHECKING:
    from junifer.storage import BaseFeatureStorage


@register_marker
class FunctionalConnectivityAtlas(BaseMarker):
    """Class for functional connectivity.

    Parameters
    ----------
    atlas : str
        The name of the atlas. Check valid options by calling
        :func:`junifer.data.list_atlases`.
    agg_method : str, optional
        The method to perform aggregation using. Check valid options in
        :func:`junifer.stats.get_aggfunc_by_name` (default "mean").
    agg_method_params : dict, optional
        Parameters to pass to the aggregation function. Check valid options in
        :func:`junifer.stats.get_aggfunc_by_name` (default None).
    cor_method : str, optional
        The method to perform correlation using. Check valid options in
        :func:`nilearn.connectome.ConnectivityMeasure` (default "covariance").
    cor_method_params : dict, optional
        Parameters to pass to the correlation function. Check valid options in
        :func:`nilearn.connectome.ConnectivityMeasure` (default None).
    name : str, optional
        The name of the marker. If None, will use the class name (default
        None).

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

    def compute(
        self,
        input: Dict[str, Any],
        extra_input: Optional[Dict] = None,
    ) -> Dict:
        """Compute.

        Parameters
        ----------
        input : dict
            A single input from the pipeline data object in which to compute
            the marker.
        extra_input : dict, optional
            The other fields in the pipeline data object. Useful for accessing
            other data kind that needs to be used in the computation. For
            example, the functional connectivity markers can make use of the
            confounds if available (default None).

        Returns
        -------
        dict
            The computed result as dictionary. The following data will be
            included in the dictionary:
            - data: functional connectivity matrix as a numpy.ndarray.
            - row_names: row names as a list
            - col_names: column names as a list
            - matrix_kind: the kind of matrix (tril, triu or full)

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
                kind=self.cor_method,
            )
        else:
            cm = ConnectivityMeasure(kind=self.cor_method)
        out = {}
        out["data"] = cm.fit_transform([ts["data"]])[0]
        # create column names
        out["row_names"] = ts["columns"]
        out["col_names"] = ts["columns"]
        out["matrix_kind"] = "tril"
        return out

    def store(
        self,
        kind: str,
        out: Dict[str, Any],
        storage: "BaseFeatureStorage",
    ) -> None:
        """Store.

        Parameters
        ----------
        kind : {"BOLD"}
            The data kind to store.
        out : dict
            The computed result as a dictionary to store.
        storage : storage-like
            The storage class, for example, SQLiteFeatureStorage.

        """
        logger.debug(f"Storing {kind} in {storage}")
        storage.store_matrix2d(**out)
