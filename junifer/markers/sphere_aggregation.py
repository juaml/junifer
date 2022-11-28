"""Provide class for sphere aggregation."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Any, Dict, List, Optional, Union

from ..api.decorators import register_marker
from ..data import load_coordinates, load_mask
from ..external.nilearn import JuniferNiftiSpheresMasker
from ..stats import get_aggfunc_by_name
from ..utils import logger
from .base import BaseMarker


@register_marker
class SphereAggregation(BaseMarker):
    """Class for sphere aggregation.

    Parameters
    ----------
    coords : str
        The name of the coordinates list to use. See
        :func:`junifer.data.coordinates.list_coordinates` for options.
    radius : float, optional
        The radius of the sphere in millimeters. If None, the signal will be
        extracted from a single voxel. See
        :class:`nilearn.maskers.NiftiSpheresMasker` for more information
        (default None).
    method : str, optional
        The aggregation method to use.
        See :func:`junifer.stats.get_aggfunc_by_name` for more information
        (default "mean").
    method_params : dict, optional
        The parameters to pass to the aggregation method (default None).
    mask : str, optional
        The name of the mask to apply to regions before extracting signals.
        Check valid options by calling :func:`junifer.data.masks.list_masks`
        (default None).
    on : {"T1w", "BOLD", "VBM_GM", "VBM_WM", "fALFF", "GCOR", "LCOR"} or \
         list of the options, optional
        The data types to apply the marker to. If None, will work on all
        available data (default None).
    name : str, optional
        The name of the marker. By default, it will use KIND_SphereAggregation
        where KIND is the kind of data it was applied to (default None).

    """

    _DEPENDENCIES = {"nilearn", "numpy"}

    def __init__(
        self,
        coords: str,
        radius: Optional[float] = None,
        method: str = "mean",
        method_params: Optional[Dict[str, Any]] = None,
        mask: Optional[str] = None,
        on: Union[List[str], str, None] = None,
        name: Optional[str] = None,
    ) -> None:
        self.coords = coords
        self.radius = radius
        self.method = method
        self.method_params = method_params or {}
        self.mask = mask
        super().__init__(on=on, name=name)

    def get_valid_inputs(self) -> List[str]:
        """Get valid data types for input.

        Returns
        -------
        list of str
            The list of data types that can be used as input for this marker.

        """
        return ["T1w", "BOLD", "VBM_GM", "VBM_WM", "fALFF", "GCOR", "LCOR"]

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

        if input_type in ["VBM_GM", "VBM_WM", "fALFF", "GCOR", "LCOR"]:
            return "table"
        elif input_type == "BOLD":
            return "timeseries"
        else:
            raise ValueError(f"Unknown input kind for {input_type}")

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

            * ``data`` : the actual computed values as a numpy.ndarray
            * ``columns`` : the column labels for the computed values as a list
            * ``row_names`` (if more than one row is present in data): "scan"

        """
        t_input = input["data"]
        logger.debug(f"Sphere aggregation using {self.method}")
        # Get aggregation function
        agg_func = get_aggfunc_by_name(
            self.method, func_params=self.method_params
        )
        # Load mask
        mask_img = None
        if self.mask is not None:
            logger.debug(f"Masking with {self.mask}")
            mask_img, _ = load_mask(self.mask)
        # Get seeds and labels
        coords, out_labels = load_coordinates(name=self.coords)
        masker = JuniferNiftiSpheresMasker(
            seeds=coords,
            radius=self.radius,
            mask_img=mask_img,
            agg_func=agg_func,
        )
        # Fit and transform the marker on the data
        out_values = masker.fit_transform(t_input)
        # Format the output
        out = {"data": out_values, "columns": out_labels}
        return out
