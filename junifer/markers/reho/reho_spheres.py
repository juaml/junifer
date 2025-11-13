"""Provide class for regional homogeneity (ReHo) on spheres."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Any, Literal, Optional, Union

import numpy as np
from pydantic import PositiveFloat

from ...api.decorators import register_marker
from ...datagrabber import DataType
from ...utils import logger
from ..sphere_aggregation import SphereAggregation
from .reho_base import ReHoBase


__all__ = ["ReHoSpheres"]


@register_marker
class ReHoSpheres(ReHoBase):
    """Class for regional homogeneity on spheres.

    Parameters
    ----------
    coords : str
        The name of the coordinates list to use.
        See :func:`.list_data` for options.
    using : :enum:`.ReHoImpl`
    radius : ``zero`` or positive float or None, optional
        The radius of the sphere in millimetres.
        If None, the signal will be extracted from a single voxel.
        See :class:`.JuniferNiftiSpheresMasker` for more information
        (default None).
    allow_overlap : bool, optional
        Whether to allow overlapping spheres.
        If False, an error is raised if the spheres overlap (default False).
    reho_params : dict or None, optional
        Extra parameters for computing ReHo map as a dictionary (default None).
        If ``using=ReHoImpl.afni``, then the valid keys are:

        * ``nneigh`` : {7, 19, 27}, optional (default 27)
            Number of voxels in the neighbourhood, inclusive. Can be:

            - 7 : for facewise neighbours only
            - 19 : for face- and edge-wise neighbours
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

        else if ``using=ReHoImpl.junifer``, then the valid keys are:

        * ``nneigh`` : {7, 19, 27, 125}, optional (default 27)
            Number of voxels in the neighbourhood, inclusive. Can be:

            * 7 : for facewise neighbours only
            * 19 : for face- and edge-wise neighbours
            * 27 : for face-, edge-, and node-wise neighbors
            * 125 : for 5x5 cuboidal volume

    agg_method : str, optional
        The aggregation function to use.
        See :func:`.get_aggfunc_by_name` for options
        (default "mean").
    agg_method_params : dict or None, optional
        The parameters to pass to the aggregation function.
        See :func:`.get_aggfunc_by_name` for options (default None).
    masks : list of dict or str, or None, optional
        The specification of the masks to apply to regions before extracting
        signals. Check :ref:`Using Masks <using_masks>` for more details.
        If None, will not apply any mask (default None).
    name : str or None, optional
        The name of the marker.
        If None, it will use the class name (default None).

    """

    coords: str
    radius: Optional[Union[Literal[0], PositiveFloat]] = None
    allow_overlap: bool = False
    on: list[Literal[DataType.BOLD]] = [DataType.BOLD]  # noqa: RUF012

    def compute(
        self,
        input: dict[str, Any],
        extra_input: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
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
            The computed result as dictionary. This will be either returned
            to the user or stored in the storage by calling the store method
            with this as a parameter. The dictionary has the following keys:

            * ``reho`` : dictionary with the following keys:

              - ``data`` : ROI values as ``numpy.ndarray``
              - ``col_names`` : ROI labels as list of str

        """
        logger.info("Calculating ReHo for spheres")

        # Compute voxelwise reho
        # If the input data space is "native", then reho_file_path points to
        # the input data path as it might be required for coordinates
        # transformation to native space.
        if self.reho_params is not None:
            reho_map, reho_file_path = self._compute(
                input_data=input, **self.reho_params
            )
        else:
            reho_map, reho_file_path = self._compute(input_data=input)

        # Perform aggregation on reho map
        aggregation_input = dict(input.items())
        aggregation_input["data"] = reho_map
        aggregation_input["path"] = reho_file_path
        sphere_aggregation = SphereAggregation(
            coords=self.coords,
            radius=self.radius,
            allow_overlap=self.allow_overlap,
            method=self.agg_method,
            method_params=self.agg_method_params,
            masks=self.masks,
            on=[DataType.BOLD],
        ).compute(input=aggregation_input, extra_input=extra_input)

        return {
            "reho": {
                # Only use the first row and expand row dimension
                "data": sphere_aggregation["aggregation"]["data"][0][
                    np.newaxis, :
                ],
                "col_names": sphere_aggregation["aggregation"]["col_names"],
            }
        }
