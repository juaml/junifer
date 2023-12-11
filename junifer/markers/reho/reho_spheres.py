"""Provide class for regional homogeneity (ReHo) on spheres."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL


from typing import Any, Dict, List, Optional, Union

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
        :func:`.list_coordinates` for options.
    radius : float, optional
        The radius of the sphere in millimeters. If None, the signal will be
        extracted from a single voxel. See
        :class:`nilearn.maskers.NiftiSpheresMasker` for more information
        (default None).
    allow_overlap : bool, optional
        Whether to allow overlapping spheres. If False, an error is raised if
        the spheres overlap (default is False).
    use_afni : bool, optional
        Whether to use AFNI for computing. If None, will use AFNI only
        if available (default None).
    reho_params : dict, optional
        Extra parameters for computing ReHo map as a dictionary (default None).
        If ``use_afni = True``, then the valid keys are:

        * ``nneigh`` : {7, 19, 27}, optional (default 27)
            Number of voxels in the neighbourhood, inclusive. Can be:

            - 7 : for facewise neighbours only
            - 19 : for face- and edge-wise nieghbours
            - 27 : for face-, edge-, and node-wise neighbors

        * ``neigh_rad`` : positive float, optional
            The radius of a desired neighbourhood (default None).
        * ``neigh_x`` : positive float, optional
            The semi-radius for x-axis of ellipsoidal volumes (default None).
        * ``neigh_y`` : positive float, optional
            The semi-radius for y-axis of ellipsoidal volumes (default None).
        * ``neigh_z`` : positive float, optional
            The semi-radius for z-axis of ellipsoidal volumes (default None).
        * ``box_rad`` : positive int, optional
            The number of voxels outward in a given cardinal direction for a
            cubic box centered on a given voxel (default None).
        * ``box_x`` : positive int, optional
            The number of voxels for +/- x-axis of cuboidal volumes
            (default None).
        * ``box_y`` : positive int, optional
            The number of voxels for +/- y-axis of cuboidal volumes
            (default None).
        * ``box_z`` : positive int, optional
            The number of voxels for +/- z-axis of cuboidal volumes
            (default None).

        else if ``use_afni = False``, then the valid keys are:

        * ``nneigh`` : {7, 19, 27, 125}, optional (default 27)
            Number of voxels in the neighbourhood, inclusive. Can be:

            * 7 : for facewise neighbours only
            * 19 : for face- and edge-wise nieghbours
            * 27 : for face-, edge-, and node-wise neighbors
            * 125 : for 5x5 cuboidal volume

    agg_method : str, optional
        The aggregation method to use.
        See :func:`.get_aggfunc_by_name` for more information
        (default None).
    agg_method_params : dict, optional
        The parameters to pass to the aggregation method (default None).
    masks : str, dict or list of dict or str, optional
        The specification of the masks to apply to regions before extracting
        signals. Check :ref:`Using Masks <using_masks>` for more details.
        If None, will not apply any mask (default None).
    name : str, optional
        The name of the marker. If None, it will use the class name
        (default None).

    """

    def __init__(
        self,
        coords: str,
        radius: Optional[float] = None,
        allow_overlap: bool = False,
        use_afni: Optional[bool] = None,
        reho_params: Optional[Dict] = None,
        agg_method: str = "mean",
        agg_method_params: Optional[Dict] = None,
        masks: Union[str, Dict, List[Union[Dict, str]], None] = None,
        name: Optional[str] = None,
    ) -> None:
        self.coords = coords
        self.radius = radius
        self.allow_overlap = allow_overlap
        self.reho_params = reho_params
        self.agg_method = agg_method
        self.agg_method_params = agg_method_params
        self.masks = masks
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
            * ``col_names`` : the column labels for the spheres as a list

        """
        logger.info("Calculating ReHo for spheres.")
        # Calculate reho map
        if self.reho_params is not None:
            reho_map, reho_file_path = self.compute_reho_map(
                input=input, **self.reho_params
            )
        else:
            reho_map, reho_file_path = self.compute_reho_map(input=input)
        # Initialize sphere aggregation
        sphere_aggregation = SphereAggregation(
            coords=self.coords,
            radius=self.radius,
            allow_overlap=self.allow_overlap,
            method=self.agg_method,
            method_params=self.agg_method_params,
            masks=self.masks,
            on="BOLD",
        )
        # Perform aggregation on reho map
        sphere_aggregation_input = dict(input.items())
        sphere_aggregation_input["data"] = reho_map
        sphere_aggregation_input["path"] = reho_file_path
        output = sphere_aggregation.compute(
            input=sphere_aggregation_input, extra_input=extra_input
        )
        # Only use the first row and expand row dimension
        output["data"] = output["data"][0][np.newaxis, :]
        return output
