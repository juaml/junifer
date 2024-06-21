"""Provide abstract base class for functional connectivity (FC)."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL


from abc import abstractmethod
from typing import Any, ClassVar, Dict, List, Optional, Set, Union

from sklearn.covariance import EmpiricalCovariance, LedoitWolf

from ...external.nilearn import JuniferConnectivityMeasure
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

    _DEPENDENCIES: ClassVar[Set[str]] = {"nilearn", "scikit-learn"}

    def __init__(
        self,
        agg_method: str = "mean",
        agg_method_params: Optional[Dict] = None,
        conn_method: str = "correlation",
        conn_method_params: Optional[Dict] = None,
        masks: Union[str, Dict, List[Union[Dict, str]], None] = None,
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
        input: Dict[str, Any],
        extra_input: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Perform aggregation."""
        raise_error(
            msg="Concrete classes need to implement aggregate().",
            klass=NotImplementedError,
        )

    def get_valid_inputs(self) -> List[str]:
        """Get valid data types for input.

        Returns
        -------
        list of str
            The list of data types that can be used as input for this marker.

        """
        return ["BOLD"]

    def get_output_type(self, input_type: str) -> str:
        """Get output type.

        Parameters
        ----------
        input_type : str
            The data type input to the marker.

        Returns
        -------
        str
            The storage type output by the marker.

        """
        return "matrix"

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
            The computed result as dictionary. The following keys will be
            included in the dictionary:

            * ``data`` : functional connectivity matrix as a ``numpy.ndarray``.
            * ``row_names`` : row names as a list
            * ``col_names`` : column names as a list
            * ``matrix_kind`` : the kind of matrix (tril, triu or full)

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
            "data": connectivity.fit_transform([aggregation["data"]])[0],
            "row_names": aggregation["col_names"],
            "col_names": aggregation["col_names"],
            "matrix_kind": "tril",
        }
