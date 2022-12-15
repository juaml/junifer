"""Provide class for regional homogeneity (ReHo) on spheres."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL


from typing import Any, Dict, Optional

import numpy as np

from ...api.decorators import register_marker
from ...utils import logger
from ..sphere_aggregation import SphereAggregation
from .reho_base import ReHoBase


@register_marker
class ReHoSpheres(ReHoBase):
    """Class for regional homogeneity on spheres.

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
    use_afni : bool, optional
        Whether to use AFNI for computing. If None, will use AFNI only
        if available (default None).
    reho_params : dict, optional
        Extra parameters for computing ReHo map as a dictionary (default None).
    agg_method : str, optional
        The aggregation method to use.
        See :func:`junifer.stats.get_aggfunc_by_name` for more information
        (default None).
    agg_method_params : dict, optional
        The parameters to pass to the aggregation method (default None).
    mask : str, optional
        The name of the mask to apply to regions before extracting signals.
        Check valid options by calling :func:`junifer.data.masks.list_masks`
        (default None).
    name : str, optional
        The name of the marker. If None, it will use the class name
        (default None).

    """

    def __init__(
        self,
        coords: str,
        radius: Optional[float] = None,
        use_afni: Optional[bool] = None,
        reho_params: Optional[Dict] = None,
        agg_method: str = "mean",
        agg_method_params: Optional[Dict] = None,
        mask: Optional[str] = None,
        name: Optional[str] = None,
    ) -> None:
        self.coords = coords
        self.radius = radius
        self.reho_params = reho_params
        self.agg_method = agg_method
        self.agg_method_params = agg_method_params
        self.mask = mask
        super().__init__(use_afni=use_afni, name=name)

    def compute(
        self,
        input: Dict[str, Any],
        extra_input: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Compute.

        Parameters
        ----------
        input : dict
            The BOLD data as dictionary.
        extra_input : dict, optional
            The other fields in the pipeline data object (default None).

        Returns
        -------
        dict
            The computed result as dictionary. The dictionary has the following
            keys:

            * ``data`` : the actual computed values as a 1D numpy.ndarray
            * ``columns`` : the column labels for the spheres as a list
            * ``rows_col_name`` : ``None``

        """
        logger.info("Calculating ReHO for spheres.")
        # Calculate reho map
        if self.reho_params is not None:
            reho_map = self.compute_reho_map(input=input, **self.reho_params)
        else:
            reho_map = self.compute_reho_map(input=input)
        # Initialize sphere aggregation
        sphere_aggregation = SphereAggregation(
            coords=self.coords,
            radius=self.radius,
            method=self.agg_method,
            method_params=self.agg_method_params,
            mask=self.mask,
            on="BOLD",
        )
        # Perform aggregation on reho map
        sphere_aggregation_input = {"data": reho_map}
        output = sphere_aggregation.compute(input=sphere_aggregation_input)
        # Only use the first row and expand row dimension
        output["data"] = output["data"][0][np.newaxis, :]
        return output
