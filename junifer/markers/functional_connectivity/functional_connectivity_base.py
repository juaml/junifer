"""Provide abstract base class for functional connectivity (FC)."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL


from abc import abstractmethod
from typing import Any, ClassVar, Dict, List, Optional, Set, Union

from nilearn.connectome import ConnectivityMeasure
from sklearn.covariance import EmpiricalCovariance

from ...utils import raise_error
from ..base import BaseMarker


__all__ = ["FunctionalConnectivityBase"]


class FunctionalConnectivityBase(BaseMarker):
    """Abstract base class for functional connectivity markers.

    Parameters
    ----------
    agg_method : str, optional
        The method to perform aggregation using. Check valid options in
        :func:`.get_aggfunc_by_name` (default "mean").
    agg_method_params : dict, optional
        Parameters to pass to the aggregation function. Check valid options in
        :func:`.get_aggfunc_by_name` (default None).
    cor_method : str, optional
        The method to perform correlation using. Check valid options in
        :class:`nilearn.connectome.ConnectivityMeasure`
        (default "covariance").
    cor_method_params : dict, optional
        Parameters to pass to the correlation function. Check valid options in
        :class:`nilearn.connectome.ConnectivityMeasure` (default None).
    masks : str, dict or list of dict or str, optional
        The specification of the masks to apply to regions before extracting
        signals. Check :ref:`Using Masks <using_masks>` for more details.
        If None, will not apply any mask (default None).
    name : str, optional
        The name of the marker. If None, will use the class name (default
        None).

    """

    _DEPENDENCIES: ClassVar[Set[str]] = {"nilearn", "scikit-learn"}

    _MARKER_INOUT_MAPPINGS: ClassVar[Dict[str, Dict[str, str]]] = {
        "BOLD": {
            "functional_connectivity": "matrix",
        },
    }

    def __init__(
        self,
        agg_method: str = "mean",
        agg_method_params: Optional[Dict] = None,
        cor_method: str = "covariance",
        cor_method_params: Optional[Dict] = None,
        masks: Union[str, Dict, List[Union[Dict, str]], None] = None,
        name: Optional[str] = None,
    ) -> None:
        self.agg_method = agg_method
        self.agg_method_params = agg_method_params
        self.cor_method = cor_method
        self.cor_method_params = cor_method_params or {}

        # default to nilearn behavior
        self.cor_method_params["empirical"] = self.cor_method_params.get(
            "empirical", False
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
        # Compute correlation
        if self.cor_method_params["empirical"]:
            connectivity = ConnectivityMeasure(
                cov_estimator=EmpiricalCovariance(),  # type: ignore
                kind=self.cor_method,
            )
        else:
            connectivity = ConnectivityMeasure(kind=self.cor_method)
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
