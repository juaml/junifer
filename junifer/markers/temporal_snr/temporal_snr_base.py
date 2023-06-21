"""Provide abstract base class for temporal signal-to-noise ratio (tSNR)."""

# Authors: Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL


from abc import abstractmethod
from typing import Any, ClassVar, Dict, List, Optional, Set, Union

from nilearn import image as nimg

from ...utils import raise_error
from ..base import BaseMarker


class TemporalSNRBase(BaseMarker):
    """Abstract base class for temporal SNR markers.

    Parameters
    ----------
    agg_method : str, optional
        The method to perform aggregation using. Check valid options in
        :func:`.get_aggfunc_by_name` (default "mean").
    agg_method_params : dict, optional
        Parameters to pass to the aggregation function. Check valid options in
        :func:`.get_aggfunc_by_name` (default None).
    masks : str, dict or list of dict or str, optional
        The specification of the masks to apply to regions before extracting
        signals. Check :ref:`Using Masks <using_masks>` for more details.
        If None, will not apply any mask (default None).
    name : str, optional
        The name of the marker. If None, will use the class name (default
        None).

    """

    _DEPENDENCIES: ClassVar[Set[str]] = {"nilearn"}

    def __init__(
        self,
        agg_method: str = "mean",
        agg_method_params: Optional[Dict] = None,
        masks: Union[str, Dict, List[Union[Dict, str]], None] = None,
        name: Optional[str] = None,
    ) -> None:
        self.agg_method = agg_method
        self.agg_method_params = agg_method_params
        self.masks = masks
        super().__init__(on="BOLD", name=name)

    @abstractmethod
    def aggregate(
        self, input: Dict[str, Any], extra_input: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Perform aggregation."""
        raise_error(
            msg="Concrete classes need to implement aggregate().",
            klass=NotImplementedError,
        )

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
        return "vector"

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
            other data kind that needs to be used in the computation.

        Returns
        -------
        dict
            The computed result as dictionary. The following keys will be
            included in the dictionary:

            * ``data`` : the computed values as a ``numpy.ndarray``
            * ``col_names`` : the column labels for the computed values as list

        """
        # Calculate voxelwise temporal signal-to-noise ratio in an image
        mean_img = nimg.math_img(
            "img.mean(axis=-1).squeeze()", img=input["data"]
        )
        stdv_img = nimg.math_img(
            "img.std(axis=-1).squeeze()", img=input["data"]
        )
        mask_img = nimg.math_img("(stdv_img != 0)", stdv_img=stdv_img)
        input["data"] = nimg.math_img(
            "np.divide(mean_img, stdv_img, where=mask_img.astype(bool))",
            mean_img=mean_img,
            stdv_img=stdv_img,
            mask_img=mask_img,
        )
        # Perform necessary aggregation and return
        return self.aggregate(input=input, extra_input=extra_input)
