"""Provide class for temporal SNR using spheres."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL

from typing import Any, Optional, Union

from ...api.decorators import register_marker
from ..sphere_aggregation import SphereAggregation
from ..utils import raise_error
from .temporal_snr_base import TemporalSNRBase


__all__ = ["TemporalSNRSpheres"]


@register_marker
class TemporalSNRSpheres(TemporalSNRBase):
    """Class for temporal signal-to-noise ratio using coordinates (spheres).

    Parameters
    ----------
    coords : str
        The name of the coordinates list to use.
        See :func:`.list_data` for options.
    radius : float, optional
        The radius of the sphere in mm. If None, the signal will be extracted
        from a single voxel. See :class:`nilearn.maskers.NiftiSpheresMasker`
        for more information (default None).
    allow_overlap : bool, optional
        Whether to allow overlapping spheres. If False, an error is raised if
        the spheres overlap (default is False).
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
        The name of the marker. By default, it will use
        KIND_FunctionalConnectivitySpheres where KIND is the kind of data it
        was applied to (default None).

    """

    def __init__(
        self,
        coords: str,
        radius: Optional[float] = None,
        allow_overlap: bool = False,
        agg_method: str = "mean",
        agg_method_params: Optional[dict] = None,
        masks: Union[str, dict, list[Union[dict, str]], None] = None,
        name: Optional[str] = None,
    ) -> None:
        self.coords = coords
        self.radius = radius
        self.allow_overlap = allow_overlap
        if radius is None or radius <= 0:
            raise_error(f"radius should be > 0: provided {radius}")
        super().__init__(
            agg_method=agg_method,
            agg_method_params=agg_method_params,
            masks=masks,
            name=name,
        )

    def aggregate(
        self, input: dict[str, Any], extra_input: Optional[dict] = None
    ) -> dict:
        """Perform sphere aggregation.

        Parameters
        ----------
        input : dict
            A single input from the pipeline data object in which the data
            is the voxelwise temporal SNR map.
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

                - ``data`` : ROI-wise tSNR values as ``numpy.ndarray``
                - ``col_names`` : ROI labels as list of str

        """
        return SphereAggregation(
            coords=self.coords,
            radius=self.radius,
            allow_overlap=self.allow_overlap,
            method=self.agg_method,
            method_params=self.agg_method_params,
            masks=self.masks,
            on="BOLD",
        ).compute(input=input, extra_input=extra_input)
