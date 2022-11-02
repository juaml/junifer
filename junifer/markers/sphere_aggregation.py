"""Provide class for sphere aggregation."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from nilearn.maskers import NiftiSpheresMasker

from ..api.decorators import register_marker
from ..data import load_coordinates
from ..utils import logger, raise_error
from .base import BaseMarker


if TYPE_CHECKING:
    from junifer.storage import BaseFeatureStorage


@register_marker
class SphereAggregation(BaseMarker):
    """Class for sphere aggregation.

    Parameters
    ----------
    coords: str
        The name of the coordinates list to use. See
        :func:`junifer.data.list_coordinates` for options.
    radius: float, optional
        The radius of the sphere in mm. If None, the signal will be extracted
        from a single voxel. See :class:`nilearn.maskers.NiftiSpheresMasker`
        for more information (default None).
    method: str, optional
        The aggregation method to use.
        See :func:`junifer.stats.get_aggfunc_by_name` for more information
        (default "mean").
    method_params: dict, optional
        The parameters to pass to the aggregation method (default None).
    on: list of str, optional
        The kind of data to apply the marker to. By default, will work on all
        available data (default None).
    name : str, optional
        The name of the marker. By default, it will use KIND_SphereAggregation
        where KIND is the kind of data it was applied to (default None).

    """

    def __init__(
        self,
        coords: str,
        radius: Optional[float] = None,
        method: str = "mean",
        method_params: Optional[Dict] = None,
        on: Optional[List[str]] = None,
        name: Optional[str] = None,
    ) -> None:
        """Initialize the class."""
        self.coords = coords
        self.radius = radius

        if method != "mean":
            raise_error(
                "Only mean aggregation is supported for sphere aggregation. "
                "If you need other aggregation methods, please open an issue "
                "on `junifer github`_.",
                NotImplementedError,
            )

        self.method = method
        self.method_params = {} if method_params is None else method_params
        super().__init__(on=on, name=name)

    def get_valid_inputs(self) -> List[str]:
        """Get valid data types for input.

        Returns
        -------
        list of str
            The list of data types that can be used as input for this marker

        """
        return ["T1w", "BOLD", "VBM_GM", "VBM_WM", "fALFF", "GCOR", "LCOR"]

    def get_output_kind(self, input: List[str]) -> List[str]:
        """Get output kind.

        Parameters
        ----------
        input : list of str
            The kind of data to work on.

        Returns
        -------
        list of str
            The kind of output.

        """
        outputs = []
        for t_input in input:
            if t_input in ["VBM_GM", "VBM_WM", "fALFF", "GCOR", "LCOR"]:
                outputs.append("table")
            elif t_input in ["BOLD"]:
                outputs.append("timeseries")
            else:
                raise ValueError(f"Unknown input kind for {t_input}")
        return outputs

    def store(
        self,
        kind: str,
        out: Dict[str, Any],
        storage: "BaseFeatureStorage",
    ) -> None:
        """Store.

        Parameters
        ----------
        kind : {"BOLD", "VBM_GM", "VBM_WM", "fALFF", "GCOR", "LCOR"}
            The data kind to store.
        out : dict
            The computed result as a dictionary to store.
        storage : storage-like
            The storage class, for example, SQLiteFeatureStorage.

        """
        logger.debug(f"Storing {kind} in {storage}")
        if kind in ["VBM_GM", "VBM_WM", "fALFF", "GCOR", "LCOR"]:
            storage.store(kind="table", **out)
        elif kind in ["BOLD"]:
            storage.store(kind="timeseries", **out)

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
            - data : the actual computed values as a numpy.ndarray
            - columns : the column labels for the computed values as a list
            - row_names (if more than one row is present in data): "scan"

        """
        t_input = input["data"]
        logger.debug(f"Sphere aggregation using {self.method}")
        # agg_func = get_aggfunc_by_name(
        #     self.method, func_params=self.method_params
        # )
        coords, out_labels = load_coordinates(self.coords)
        masker = NiftiSpheresMasker(
            seeds=coords,
            radius=self.radius,
            mask_img=None,  # TODO: support this (needs #79)
        )

        out_values = masker.fit_transform(t_input)
        out = {"data": out_values, "columns": out_labels}
        if out_values.shape[0] > 1:
            out["row_names"] = "scan"
        return out
