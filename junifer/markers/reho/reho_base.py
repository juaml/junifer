"""Provide base class for regional homogeneity (ReHo)."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from enum import Enum
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Literal,
    Optional,
    Union,
)

from ...datagrabber import DataType
from ...storage import StorageType
from ...typing import ConditionalDependencies, MarkerInOutMappings
from ...utils import logger
from ..base import BaseMarker
from ._afni_reho import AFNIReHo
from ._junifer_reho import JuniferReHo


if TYPE_CHECKING:
    from nibabel.nifti1 import Nifti1Image


__all__ = ["ReHoBase", "ReHoImpl"]


class ReHoImpl(str, Enum):
    """Accepted ReHo implementations.

    * ``junifer`` : ``junifer``'s ReHo
    * ``afni`` : AFNI's ``3dReHo``

    """

    junifer = "junifer"
    afni = "afni"


class ReHoBase(BaseMarker):
    """Base class for regional homogeneity computation.

    Parameters
    ----------
    using : :enum:`.ReHoImpl`
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

    _CONDITIONAL_DEPENDENCIES: ClassVar[ConditionalDependencies] = [
        {
            "depends_on": AFNIReHo,
            "using": ReHoImpl.afni,
        },
        {
            "depends_on": JuniferReHo,
            "using": ReHoImpl.junifer,
        },
    ]

    _MARKER_INOUT_MAPPINGS: ClassVar[MarkerInOutMappings] = {
        DataType.BOLD: {
            "reho": StorageType.Vector,
        },
    }

    using: ReHoImpl
    reho_params: Optional[dict] = None
    agg_method: str = "mean"
    agg_method_params: Optional[dict] = None
    masks: Optional[list[Union[dict, str]]] = None
    on: list[Literal[DataType.BOLD]] = [DataType.BOLD]  # noqa: RUF012

    def _compute(
        self,
        input_data: dict[str, Any],
        **reho_params: Any,
    ) -> tuple["Nifti1Image", Path]:
        """Compute voxel-wise ReHo.

        Calculates Kendall's W per voxel using neighborhood voxels.
        Instead of the time series values themselves, Kendall's W uses the
        relative rank ordering of a hood over all time points to evaluate
        a parameter W in range 0-1, with 0 reflecting no trend of agreement
        between time series and 1 reflecting perfect agreement. For more
        information about the method, please check [1]_.

        Parameters
        ----------
        input_data : dict
            The BOLD data as dictionary.
        **reho_params : dict
            Extra keyword arguments for ReHo.

        Returns
        -------
        Niimg-like object
            The ReHo map as NIfTI.
        pathlib.Path
            The path to the ReHo map as NIfTI or the input data path if the
            input data space is "native".

        References
        ----------
        .. [1] Jiang, L., & Zuo, X. N. (2016).
               Regional Homogeneity: A Multimodal, Multiscale Neuroimaging
               Marker of the Human Connectome.
               The Neuroscientist, Volume 22(5), Pages 486-505.
               https://doi.org/10.1177/1073858415595004

        """
        logger.debug("Calculating voxel-wise ReHo")

        # Conditional estimator
        if self.using == "afni":
            estimator = AFNIReHo()
        elif self.using == "junifer":
            estimator = JuniferReHo()
        # Compute reho
        reho_map, reho_map_path = estimator.compute(  # type: ignore
            input_path=input_data["path"],
            **reho_params,
        )

        # If the input data space is native already, the original path should
        # be propagated down as it might be required for transforming
        # parcellation / coordinates to native space, else the reho map
        # path should be passed for use later if required.
        # TODO(synchon): will be taken care in #292
        if input_data["space"] == "native":
            return reho_map, input_data["path"]

        return reho_map, reho_map_path
