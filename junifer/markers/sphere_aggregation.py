"""Provide class for sphere aggregation."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Any, ClassVar, Optional, Union

from ..api.decorators import register_marker
from ..data import get_data
from ..external.nilearn import JuniferNiftiSpheresMasker
from ..stats import get_aggfunc_by_name
from ..typing import Dependencies, MarkerInOutMappings
from ..utils import logger, raise_error, warn_with_log
from .base import BaseMarker


__all__ = ["SphereAggregation"]


@register_marker
class SphereAggregation(BaseMarker):
    """Class for sphere aggregation.

    Parameters
    ----------
    coords : str
        The name of the coordinates list to use.
        See :func:`.list_data` for options.
    radius : float, optional
        The radius of the sphere in millimeters. If None, the signal will be
        extracted from a single voxel. See
        :class:`nilearn.maskers.NiftiSpheresMasker` for more information
        (default None).
    allow_overlap : bool, optional
        Whether to allow overlapping spheres. If False, an error is raised if
        the spheres overlap (default is False).
    method : str, optional
        The aggregation method to use.
        See :func:`.get_aggfunc_by_name` for more information
        (default "mean").
    method_params : dict, optional
        The parameters to pass to the aggregation method (default None).
    time_method : str, optional
        The method to use to aggregate the time series over the time points,
        after applying :term:`method` (only applicable to BOLD data). If None,
        it will not operate on the time dimension (default None).
    time_method_params : dict, optional
        The parameters to pass to the time aggregation method (default None).
    masks : str, dict or list of dict or str, optional
        The specification of the masks to apply to regions before extracting
        signals. Check :ref:`Using Masks <using_masks>` for more details.
        If None, will not apply any mask (default None).
    on : {"T1w", "T2w", "BOLD", "VBM_GM", "VBM_WM", "VBM_CSF", "fALFF", \
        "GCOR", "LCOR"} or list of the options, optional
        The data types to apply the marker to. If None, will work on all
        available data (default None).
    name : str, optional
        The name of the marker. By default, it will use KIND_SphereAggregation
        where KIND is the kind of data it was applied to (default None).

    Raises
    ------
    ValueError
        If ``time_method`` is specified for non-BOLD data or if
        ``time_method_params`` is not None when ``time_method`` is None.

    """

    _DEPENDENCIES: ClassVar[Dependencies] = {"nilearn", "numpy"}

    _MARKER_INOUT_MAPPINGS: ClassVar[MarkerInOutMappings] = {
        "T1w": {
            "aggregation": "vector",
        },
        "T2w": {
            "aggregation": "vector",
        },
        "BOLD": {
            "aggregation": "timeseries",
        },
        "VBM_GM": {
            "aggregation": "vector",
        },
        "VBM_WM": {
            "aggregation": "vector",
        },
        "VBM_CSF": {
            "aggregation": "vector",
        },
        "fALFF": {
            "aggregation": "vector",
        },
        "GCOR": {
            "aggregation": "vector",
        },
        "LCOR": {
            "aggregation": "vector",
        },
    }

    def __init__(
        self,
        coords: str,
        radius: Optional[float] = None,
        allow_overlap: bool = False,
        method: str = "mean",
        method_params: Optional[dict[str, Any]] = None,
        time_method: Optional[str] = None,
        time_method_params: Optional[dict[str, Any]] = None,
        masks: Union[str, dict, list[Union[dict, str]], None] = None,
        on: Union[list[str], str, None] = None,
        name: Optional[str] = None,
    ) -> None:
        self.coords = coords
        self.radius = radius
        self.allow_overlap = allow_overlap
        self.method = method
        self.method_params = method_params or {}
        self.masks = masks
        super().__init__(on=on, name=name)

        # Verify after super init so self._on is set
        if "BOLD" not in self._on and time_method is not None:
            raise_error(
                "`time_method` can only be used with BOLD data. "
                "Please remove `time_method` parameter."
            )
        if time_method is None and time_method_params is not None:
            raise_error(
                "`time_method_params` can only be used with `time_method`. "
                "Please remove `time_method_params` parameter."
            )
        self.time_method = time_method
        self.time_method_params = time_method_params or {}

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

            * ``aggregation`` : dictionary with the following keys:

                - ``data`` : ROI values as ``numpy.ndarray``
                - ``col_names`` : ROI labels as list of str

        Warns
        -----
        RuntimeWarning
            If time aggregation is required but only time point is available.

        """
        t_input_img = input["data"]
        logger.debug(f"Sphere aggregation using {self.method}")
        # Get aggregation function
        agg_func = get_aggfunc_by_name(
            self.method, func_params=self.method_params
        )

        # Get seeds and labels tailored to target image
        coords, labels = get_data(
            kind="coordinates",
            names=self.coords,
            target_data=input,
            extra_input=extra_input,
        )

        # Load mask
        mask_img = None
        if self.masks is not None:
            logger.debug(f"Masking with {self.masks}")
            # Get tailored mask
            mask_img = get_data(
                kind="mask",
                names=self.masks,
                target_data=input,
                extra_input=extra_input,
            )

        # Initialize masker
        logger.debug("Masking")
        masker = JuniferNiftiSpheresMasker(
            seeds=coords,
            radius=self.radius,
            allow_overlap=self.allow_overlap,
            mask_img=mask_img,
            agg_func=agg_func,
        )
        # Fit and transform the marker on the data
        out_values = masker.fit_transform(t_input_img)

        # Apply time dimension aggregation if required
        if self.time_method is not None:
            if out_values.shape[0] > 1:
                logger.debug("Aggregating time dimension")
                time_agg_func = get_aggfunc_by_name(
                    self.time_method, func_params=self.time_method_params
                )
                out_values = time_agg_func(out_values, axis=0)
            else:
                warn_with_log(
                    "No time dimension to aggregate as only one time point is "
                    "available."
                )
        # Format the output
        return {
            "aggregation": {
                "data": out_values,
                "col_names": labels,
            },
        }
