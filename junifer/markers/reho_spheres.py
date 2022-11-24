"""Provide class for regional homogeneity (ReHO) on spheres."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL


from typing import TYPE_CHECKING, Any, Dict, List, Optional

import numpy as np

from ..api.decorators import register_marker
from ..utils import logger
from .base import BaseMarker
from .sphere_aggregation import SphereAggregation


if TYPE_CHECKING:
    from junifer.storage import BaseFeatureStorage


@register_marker
class ReHOSpheres(BaseMarker):
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
    name : str, optional
        The name of the marker. If None, it will use the class name
        (default None).

    """

    def __init__(
        self,
        coords: str,
        radius: Optional[float] = None,
        name: Optional[str] = None,
    ) -> None:
        self.coords = coords
        self.radius = radius
        super().__init__(on="BOLD", name=name)

    def get_valid_inputs(self) -> List[str]:
        """Get valid data types for input.

        Returns
        -------
        list of str
            The list of data types that can be used as input for this marker.

        """
        return ["BOLD"]

    def get_output_kind(self, input: List[str]) -> List[str]:
        """Get output kind.

        Parameters
        ----------
        input : list of str
            The input to the marker. The list must contain the
            available Junifer Data dictionary keys.

        Returns
        -------
        list of str
            The updated list of output kinds, as storage possibilities.

        """
        return ["table"]

    def store(
        self,
        kind: str,
        out: Dict[str, Any],
        storage: "BaseFeatureStorage",
    ) -> None:
        """Store.

        Parameters
        ----------
        kind : {"BOLD"}
            The data kind to store.
        out : dict
            The computed result as a dictionary to store.
        storage : storage-like
            The storage class, for example, SQLiteFeatureStorage.

        """
        logger.debug(f"Storing {kind} in {storage}")
        storage.store(kind="table", **out)

    def compute(
        self,
        input: Dict[str, Any],
        extra_input: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Compute.

        For a given voxel, identifies the set of neighbours within a certain
        radius and then calculates Kendall's W for the voxel and its
        neighbours for the timepoints in the BOLD signal. For more
        information about the method, please check [1]_.

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

        References
        ----------
        .. [1] Jiang, L., & Zuo, X. N. (2016).
               Regional Homogeneity: A Multimodal, Multiscale Neuroimaging
               Marker of the Human Connectome.
               The Neuroscientist, Volume 22(5), Pages 486–505.
               https://doi.org/10.1177/1073858415595004

        """
        logger.debug("Calculating ReHO for spheres.")
        # Initialize sphere aggregation
        sphere_aggregation = SphereAggregation(
            coords=self.coords,
            radius=self.radius,
            method="kendall_w",
            on="BOLD",
        )
        # Perform aggregation
        aggregated_values = sphere_aggregation.compute(
            input=input, extra_input=extra_input
        )
        # Create a new dictionary for returning
        output = {}
        # Only use the first row and expand row dimension
        output["data"] = np.expand_dims(aggregated_values["data"][0], axis=0)
        # Set column labels
        output["columns"] = aggregated_values["columns"]
        # Set row_cols_name to None
        output["rows_col_name"] = None
        return output
