"""Provide class for sphere aggregation."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Dict, List, Optional

from nilearn.maskers import NiftiSpheresMasker

from ..api.decorators import register_marker
from ..data import load_coordinates
from ..utils import logger, raise_error
from .base import BaseMarker


@register_marker
class SphereAggregation(BaseMarker):
    """Class for sphere aggregation.

    Parameters
    ----------
    coords: str
        The name of the coordinates list to use. See junifer.data.coordinates
    radius: float
        The radius of the sphere in mm. If None, the signal will be extracted
        from a single voxel. See :class:`nilearn.maskers.NiftiSpheresMasker`
        for more information.
    method: str
        The aggregation method to use.
        See :func:`junifer.stats.get_aggfunc_by_name`
    method_params: str
        The parameters to pass to the aggregation method.
    on: list of str
        The kind of data to apply the marker to. Defaults to None, which
        means that the marker will be applied to all data.
    name

    """

    def __init__(
        self,
        coords: str,
        radius: float,
        method: str,
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
        if on is None:
            on = ["T1w", "BOLD", "VBM_GM", "VBM_WM", "fALFF", "GCOR", "LCOR"]
        super().__init__(on=on, name=name)

    def get_output_kind(self, input: List[str]) -> List[str]:
        """Get output kind.

        Parameters
        ----------
        input : list of str
            The kind of data to work on.

        Returns
        -------
        str
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

    def store(self, kind: str, out, storage) -> None:
        """Store.

        Parameters
        ----------
        kind
        out
        storage

        """
        logger.debug(f"Storing {kind} in {storage}")
        if kind in ["VBM_GM", "VBM_WM", "fALFF", "GCOR", "LCOR"]:
            storage.store_table(**out)
        if kind in ["BOLD"]:
            storage.store_timeseries(**out)

    def compute(self, input: Dict, extra_input: Optional[Dict] = None) -> Dict:
        """Compute.

        Parameters
        ----------
        input : Dict[str, Dict]
            A single input from the pipeline data object in which to compute
            the marker.
        extra_input : Dict, optional
            The other fields in the pipeline data object. Useful for accessing
            other data kind that needs to be used in the computation. For
            example, the functional connectivity markers can make use of the
            confounds if available (default None).

        Returns
        -------
        dict
            The computed result as dictionary.

        """
        t_input = input["data"]
        logger.debug(f"Sphere aggregation using {self.method}")
        # agg_func = get_aggfunc_by_name(
        #     self.method, func_params=self.method_params
        # )
        coords, out_labels = load_coordinates(self.coords)
        masker = NiftiSpheresMasker(
            coords,
            self.radius,
            mask_img=None,  # TODO: support this (needs #79)
        )

        out_values = masker.fit_transform(t_input)
        out = {"data": out_values, "columns": out_labels}
        if out_values.shape[0] > 1:
            out["row_names"] = "scan"
        return out
