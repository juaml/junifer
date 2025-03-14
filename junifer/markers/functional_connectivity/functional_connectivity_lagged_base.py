"""Provide abstract base class for lagged functional connectivity (FC)."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL


from abc import abstractmethod
from itertools import product
from typing import Any, ClassVar, Optional, Union

import numpy as np
from scipy.signal import correlate

from ...typing import Dependencies, MarkerInOutMappings
from ...utils import raise_error
from ..base import BaseMarker


__all__ = ["FunctionalConnectivityLaggedBase"]


class FunctionalConnectivityLaggedBase(BaseMarker):
    """Abstract base class for lagged functional connectivity markers.

    Parameters
    ----------
    max_lag : int
        The time lag range. The lag ranges from ``-max_lag`` to ``+max_lag``
        time points.
    agg_method : str, optional
        The method to perform aggregation using.
        Check valid options in :func:`.get_aggfunc_by_name`
        (default "mean").
    agg_method_params : dict, optional
        Parameters to pass to the aggregation function.
        Check valid options in :func:`.get_aggfunc_by_name`
        (default None).
    masks : str, dict or list of dict or str, optional
        The specification of the masks to apply to regions before extracting
        signals. Check :ref:`Using Masks <using_masks>` for more details.
        If None, will not apply any mask (default None).
    name : str, optional
        The name of the marker. If None, will use ``BOLD_<class_name>``
        (default None).

    """

    _DEPENDENCIES: ClassVar[Dependencies] = {"numpy", "scipy"}

    _MARKER_INOUT_MAPPINGS: ClassVar[MarkerInOutMappings] = {
        "BOLD": {
            "functional_connectivity": "matrix",
            "lag": "matrix",
        },
    }

    def __init__(
        self,
        max_lag: int,
        agg_method: str = "mean",
        agg_method_params: Optional[dict] = None,
        masks: Union[str, dict, list[Union[dict, str]], None] = None,
        name: Optional[str] = None,
    ) -> None:
        self.max_lag = max_lag
        self.agg_method = agg_method
        self.agg_method_params = agg_method_params
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

            * ``lag`` : dictionary with the following keys:

              - ``data`` : lag matrix as ``numpy.ndarray``
              - ``row_names`` : ROI labels as list of str
              - ``col_names`` : ROI labels as list of str
              - ``matrix_kind`` : the kind of matrix (tril, triu or full)

        Notes
        -----
        Pearson correlation is used to perform connectivity measure.

        """
        # Perform necessary aggregation
        aggregation = self.aggregate(input, extra_input=extra_input)
        # Initialize variables
        # transposed to get (n_rois, n_timepoints)
        fmri_data = aggregation["aggregation"]["data"].T
        n_rois = fmri_data.shape[0]
        fc_matrix = np.ones((n_rois, n_rois))
        lag_matrix = np.zeros((n_rois, n_rois), dtype=int)
        lags = np.arange(-self.max_lag, self.max_lag + 1)
        # Compute
        for i, j in product(range(n_rois), range(n_rois)):
            if i != j:
                # Compute cross-correlation
                ccf = correlate(
                    fmri_data[i], fmri_data[j], mode="full", method="auto"
                )
                ccf = ccf[
                    len(ccf) // 2
                    - self.max_lag : len(ccf) // 2
                    + self.max_lag
                    + 1
                ]  # Limit lag range

                # Find peak correlation and corresponding lag
                peak_idx = np.argmax(np.abs(ccf))  # Peak correlation index
                peak_corr = ccf[peak_idx]  # Peak correlation value
                peak_lag = lags[peak_idx]  # Corresponding lag
                # Store in matrices
                fc_matrix[i, j] = peak_corr
                lag_matrix[i, j] = peak_lag
        # Create dictionary for output
        roi_labels = aggregation["aggregation"]["col_names"]
        return {
            "functional_connectivity": {
                "data": fc_matrix,
                "row_names": roi_labels,
                "col_names": roi_labels,
                "matrix_kind": "full",
            },
            "lag": {
                "data": lag_matrix,
                "row_names": roi_labels,
                "col_names": roi_labels,
                "matrix_kind": "full",
            },
        }
