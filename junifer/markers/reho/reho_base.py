"""Provide base class for regional homogeneity (ReHo)."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL


from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Optional,
)

from ...typing import ConditionalDependencies, MarkerInOutMappings
from ...utils import logger, raise_error
from ..base import BaseMarker
from ._afni_reho import AFNIReHo
from ._junifer_reho import JuniferReHo


if TYPE_CHECKING:
    from nibabel.nifti1 import Nifti1Image

__all__ = ["ReHoBase"]


class ReHoBase(BaseMarker):
    """Base class for regional homogeneity computation.

    Parameters
    ----------
    using : {"junifer", "afni"}
        Implementation to use for computing ReHo:

        * "junifer" : Use ``junifer``'s own ReHo implementation
        * "afni" : Use AFNI's ``3dReHo``

    name : str, optional
        The name of the marker. If None, it will use the class name
        (default None).

    Raises
    ------
    ValueError
        If ``using`` is invalid.

    """

    _CONDITIONAL_DEPENDENCIES: ClassVar[ConditionalDependencies] = [
        {
            "using": "afni",
            "depends_on": AFNIReHo,
        },
        {
            "using": "junifer",
            "depends_on": JuniferReHo,
        },
    ]

    _MARKER_INOUT_MAPPINGS: ClassVar[MarkerInOutMappings] = {
        "BOLD": {
            "reho": "vector",
        },
    }

    def __init__(
        self,
        using: str,
        name: Optional[str] = None,
    ) -> None:
        # Validate `using` parameter
        valid_using = [dep["using"] for dep in self._CONDITIONAL_DEPENDENCIES]
        if using not in valid_using:
            raise_error(
                f"Invalid value for `using`, should be one of: {valid_using}"
            )
        self.using = using
        super().__init__(on="BOLD", name=name)

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
