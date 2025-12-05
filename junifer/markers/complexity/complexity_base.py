"""Provide base class for complexity."""

# Authors: Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from abc import abstractmethod
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    ClassVar,
    Optional,
    Union,
)

from pydantic import BeforeValidator

from ...datagrabber import DataType
from ...storage import StorageType
from ...typing import Dependencies, MarkerInOutMappings
from ...utils import ensure_list, ensure_list_or_none, raise_error
from ..base import BaseMarker
from ..parcel_aggregation import ParcelAggregation


if TYPE_CHECKING:
    import numpy as np


__all__ = ["ComplexityBase"]


class ComplexityBase(BaseMarker):
    """Abstract base class for complexity computation.

    Parameters
    ----------
    parcellation : str or list of str
        The name(s) of the parcellation(s) to use.
        See :func:`.list_data` for options.
    agg_method : str, optional
        The aggregation function to use.
        See :func:`.get_aggfunc_by_name` for options
        (default "mean").
    agg_method_params : dict or None, optional
        The parameters to pass to the aggregation function.
        See :func:`.get_aggfunc_by_name` for options (default None).
    masks : str, dict, list of them or None, optional
        The specification of the masks to apply to regions before extracting
        signals. Check :ref:`Using Masks <using_masks>` for more details.
        If None, will not apply any mask (default None).
    name : str or None, optional
        The name of the marker.
        If None, will use the class name (default None).

    """

    _DEPENDENCIES: ClassVar[Dependencies] = {"nilearn", "neurokit2"}

    _MARKER_INOUT_MAPPINGS: ClassVar[MarkerInOutMappings] = {
        DataType.BOLD: {
            "complexity": StorageType.Vector,
        },
    }

    parcellation: Annotated[
        Union[str, list[str]], BeforeValidator(ensure_list)
    ]
    agg_method: str = "mean"
    agg_method_params: Optional[dict] = None
    masks: Annotated[
        Union[dict, str, list[Union[dict, str]], None],
        BeforeValidator(ensure_list_or_none),
    ] = None

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
            on=DataType.BOLD,
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
