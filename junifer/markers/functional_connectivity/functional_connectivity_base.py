"""Provide abstract base class for functional connectivity (FC)."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL


from abc import abstractmethod
from typing import Any, ClassVar, Optional, Union

from sklearn.covariance import EmpiricalCovariance, LedoitWolf

from ...external.nilearn import JuniferConnectivityMeasure
from ...typing import Dependencies, MarkerInOutMappings
from ...utils import raise_error
from ..base import BaseMarker


__all__ = ["FunctionalConnectivityBase"]


class FunctionalConnectivityBase(BaseMarker):
    """Abstract base class for functional connectivity markers.

    Parameters
    ----------
    agg_method : str, optional
        The method to perform aggregation using.
        Check valid options in :func:`.get_aggfunc_by_name`
        (default "mean").
    agg_method_params : dict, optional
        Parameters to pass to the aggregation function.
        Check valid options in :func:`.get_aggfunc_by_name`
        (default None).
    conn_method : str, optional
        The method to perform connectivity measure using.
        Check valid options in :class:`.JuniferConnectivityMeasure`
        (default "correlation").
    conn_method_params : dict, optional
        Parameters to pass to :class:`.JuniferConnectivityMeasure`.
        If None, ``{"empirical": True}`` will be used, which would mean
        :class:`sklearn.covariance.EmpiricalCovariance` is used to compute
        covariance. If usage of :class:`sklearn.covariance.LedoitWolf` is
        desired, ``{"empirical": False}`` should be passed
        (default None).
    masks : str, dict or list of dict or str, optional
        The specification of the masks to apply to regions before extracting
        signals. Check :ref:`Using Masks <using_masks>` for more details.
        If None, will not apply any mask (default None).
    name : str, optional
        The name of the marker. If None, will use ``BOLD_<class_name>``
        (default None).

    """

    _DEPENDENCIES: ClassVar[Dependencies] = {"nilearn", "scikit-learn"}

    _MARKER_INOUT_MAPPINGS: ClassVar[MarkerInOutMappings] = {
        "BOLD": {
            "functional_connectivity": "matrix",
        },
    }

    def __init__(
        self,
        agg_method: str = "mean",
        agg_method_params: Optional[dict] = None,
        conn_method: str = "correlation",
        conn_method_params: Optional[dict] = None,
        masks: Union[str, dict, list[Union[dict, str]], None] = None,
        name: Optional[str] = None,
    ) -> None:
        self.agg_method = agg_method
        self.agg_method_params = agg_method_params
        self.conn_method = conn_method
        self.conn_method_params = conn_method_params or {}
        # Reverse of nilearn behavior
        self.conn_method_params["empirical"] = self.conn_method_params.get(
            "empirical", True
        )
        self.masks = masks
        super().__init__(on="BOLD", name=name)

    @abstractmethod
    def aggregate(
        self,
        input: dict[str, Any],
        extra_input: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Perform aggregation."""
        raise_error(
            msg="Concrete classes need to implement aggregate().",
            klass=NotImplementedError,
        )

    def compute(
        self,
        input: dict[str, Any],
        extra_input: Optional[dict] = None,
    ) -> dict:
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
            The computed result as dictionary. This will be either returned
            to the user or stored in the storage by calling the store method
            with this as a parameter. The dictionary has the following keys:

            * ``functional_connectivity`` : dictionary with the following keys:

              - ``data`` : functional connectivity matrix as ``numpy.ndarray``
              - ``row_names`` : ROI labels as list of str
              - ``col_names`` : ROI labels as list of str
              - ``matrix_kind`` : the kind of matrix (tril, triu or full)

        """
        # Perform necessary aggregation
        aggregation = self.aggregate(input, extra_input=extra_input)
        # Set covariance estimator
        if self.conn_method_params["empirical"]:
            cov_estimator = EmpiricalCovariance(store_precision=False)
        else:
            cov_estimator = LedoitWolf(store_precision=False)
        # Compute correlation
        connectivity = JuniferConnectivityMeasure(
            cov_estimator=cov_estimator,
            kind=self.conn_method,
            **{
                k: v
                for k, v in self.conn_method_params.items()
                if k != "empirical"
            },
        )
        # Create dictionary for output
        return {
            "functional_connectivity": {
                "data": connectivity.fit_transform(
                    [aggregation["aggregation"]["data"]]
                )[0],
                # Create column names
                "row_names": aggregation["aggregation"]["col_names"],
                "col_names": aggregation["aggregation"]["col_names"],
                "matrix_kind": "tril",
            },
        }
