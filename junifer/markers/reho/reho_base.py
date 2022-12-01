"""Provide base class for regional homogeneity (ReHo)."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL


from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ...utils import logger
from ..base import BaseMarker
from .reho_estimator import ReHoEstimator


if TYPE_CHECKING:
    from nibabel.imageclasses import PARRECImage


class ReHoBase(BaseMarker):
    """Base class for regional homogeneity computation.

    Parameters
    ----------
    name : str, optional
        The name of the marker. If None, it will use the class name
        (default None).

    """

    _EXT_DEPENDENCIES = [
        {"name": "afni", "optional": True, "commands": ["3dReHo"]},
    ]
    use_afni: bool = False

    def __init__(
        self,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(on="BOLD", name=name)

    def get_valid_inputs(self) -> List[str]:
        """Get valid data types for input.

        Returns
        -------
        list of str
            The list of data types that can be used as input for this marker.

        """
        return ["BOLD"]

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
        return "table"

    def compute_reho_map(
        self,
        input: Dict[str, Any],
        **reho_params: Any,
    ) -> "PARRECImage":
        """Compute.

        Calculates Kendall's W per voxel using neighborhood voxels.
        Instead of the time series values themselves, Kendall's W uses the
        relative rank ordering of a hood over all time points to evaluate
        a parameter W in range 0-1, with 0 reflecting no trend of agreement
        between time series and 1 reflecting perfect agreement. For more
        information about the method, please check [1]_.

        Parameters
        ----------
        input : dict
            The BOLD data as dictionary.
        **reho_params : dict
            Extra keyword arguments for ReHo.

        Returns
        -------
        Niimg-like object

        References
        ----------
        .. [1] Jiang, L., & Zuo, X. N. (2016).
               Regional Homogeneity: A Multimodal, Multiscale Neuroimaging
               Marker of the Human Connectome.
               The Neuroscientist, Volume 22(5), Pages 486–505.
               https://doi.org/10.1177/1073858415595004

        """
        logger.info("Calculating ReHO map.")
        # Initialize reho estimator
        reho_estimator = ReHoEstimator(use_afni=self.use_afni)
        # Fit-transform reho estimator
        reho_map = reho_estimator.fit_transform(
            input_data=input, **reho_params
        )
        return reho_map
