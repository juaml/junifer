"""Provide base class for complexity."""

# Authors: Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
# License: AGPL

from abc import abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Optional,
    Union,
)

from ...typing import Dependencies, MarkerInOutMappings
from ...utils import raise_error
from ..base import BaseMarker
from ..parcel_aggregation import ParcelAggregation


if TYPE_CHECKING:
    import numpy as np


__all__ = ["ComplexityBase"]


class ComplexityBase(BaseMarker):
    """Base class for complexity computation.

    Parameters
    ----------
    parcellation : str or list of str
        The name(s) of the parcellation(s). Check valid options by calling
        :func:`junifer.data.parcellations.list_parcellations`.
    agg_method : str, optional
        The method to perform aggregation using. Check valid options in
        :func:`junifer.stats.get_aggfunc_by_name` (default "mean").
    agg_method_params : dict, optional
        Parameters to pass to the aggregation function. Check valid options in
        :func:`junifer.stats.get_aggfunc_by_name` (default None).
    masks : str, dict or list of dict or str, optional
        The specification of the masks to apply to regions before extracting
        signals. Check :ref:`Using Masks <using_masks>` for more details.
        If None, will not apply any mask (default None).
    name : str, optional
        The name of the marker. If None, it will use the class name
        (default None).

    """

    _DEPENDENCIES: ClassVar[Dependencies] = {"nilearn", "neurokit2"}

    _MARKER_INOUT_MAPPINGS: ClassVar[MarkerInOutMappings] = {
        "BOLD": {
            "complexity": "vector",
        },
    }

    def __init__(
        self,
        parcellation: Union[str, list[str]],
        agg_method: str = "mean",
        agg_method_params: Optional[dict] = None,
        masks: Union[str, dict, list[Union[dict, str]], None] = None,
        name: Optional[str] = None,
    ) -> None:
        self.parcellation = parcellation
        self.agg_method = agg_method
        self.agg_method_params = agg_method_params
        self.masks = masks
        super().__init__(on="BOLD", name=name)

    @abstractmethod
    def compute_complexity(
        self,
        extracted_bold_values: "np.ndarray",
    ) -> "np.ndarray":
        """Compute complexity measure."""
        raise_error(
            msg="Concrete classes need to implement compute_complexity().",
            klass=NotImplementedError,
        )

    def compute(
        self,
        input: dict[str, Any],
        extra_input: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Compute.

        Parameters
        ----------
        input : dict
            A single input from the pipeline data object in which to compute
            the marker.
        extra_input : dict, optional
            The other fields in the pipeline data object. Useful for accessing
            other data kind that needs to be used in the computation.

        Returns
        -------
        dict
            The computed result as dictionary. This will be either returned
            to the user or stored in the storage by calling the store method
            with this as a parameter. The dictionary has the following keys:

           *  ``complexity`` : dictionary with the following keys:

                - ``data`` : ROI-wise complexity measures as ``numpy.ndarray``
                - ``col_names`` : ROI labels as list of str

        """
        # Extract the 2D time series using ParcelAggregation
        parcel_aggregation = ParcelAggregation(
            parcellation=self.parcellation,
            method=self.agg_method,
            method_params=self.agg_method_params,
            masks=self.masks,
            on="BOLD",
        ).compute(input=input, extra_input=extra_input)
        # Compute complexity measure
        return {
            "complexity": {
                "data": self.compute_complexity(
                    parcel_aggregation["aggregation"]["data"]
                ),
                "col_names": parcel_aggregation["aggregation"]["col_names"],
            }
        }
