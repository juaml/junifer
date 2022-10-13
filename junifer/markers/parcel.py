"""Provide class for parcel aggregation."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

import numpy as np
from nilearn.image import math_img, resample_to_img
from nilearn.maskers import NiftiMasker

from ..api.decorators import register_marker
from ..data import load_atlas
from ..stats import get_aggfunc_by_name
from ..utils import logger
from .base import BaseMarker


@register_marker
class ParcelAggregation(BaseMarker):
    """Class for parcel aggregation.

    Parameters
    ----------
    atlas : str
        The name of the atlas. Check valid options by calling
        `junifer.data.list_atlases`.
    method : str
        The method to perform aggregation using. Check valid options in
        `junifer.stats.get_aggfunc_by_name`.
    method_params : dict, optional
        Parameters to pass to the aggregation function. Check valid options in
        `junifer.stats.get_aggfunc_by_name`.
    on : {"T1w", "BOLD", "VBM_GM", "VBM_WM", "fALFF", "GCOR", "LCOR"} or list
         of the options, optional
        The kind of data to apply the marker to. If None, will work on all
        available data (default None).
    name : str, optional
        The name of the marker. If None, will use the class name (default
        None).

    """

    def __init__(
        self,
        atlas: str,
        method: str,
        method_params: Optional[Dict[str, Any]] = None,
        on: Union[List[str], str, None] = None,
        name: Optional[str] = None,
    ) -> None:
        """Initialize the class."""
        self.atlas = atlas
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

    # TODO: complete type annotations
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
            The computed result as dictionary. This will be either returned
            to the user or stored in the storage by calling the store method
            with this as a parameter.

        """
        t_input = input["data"]
        logger.debug(f"Parcel aggregation using {self.method}")
        agg_func = get_aggfunc_by_name(
            self.method, func_params=self.method_params
        )
        # Get the min of the voxels sizes and use it as the resolution
        resolution = np.min(t_input.header.get_zooms()[:3])  # type: ignore
        t_atlas, t_labels, _ = load_atlas(self.atlas, resolution=resolution)
        atlas_img_res = resample_to_img(
            t_atlas,
            t_input,
            interpolation="nearest",
        )
        atlas_bin = math_img(
            "img != 0",
            img=atlas_img_res,
        )
        logger.debug("Masking")
        masker = NiftiMasker(
            atlas_bin, target_affine=t_input.affine
        )  # type: ignore

        # Mask the input data and the atlas
        data = masker.fit_transform(t_input)
        atlas_values = masker.transform(atlas_img_res)
        atlas_values = np.squeeze(atlas_values).astype(int)

        # Get the values for each parcel and apply agg function
        logger.debug("Computing ROI means")
        atlas_roi_vals = sorted(np.unique(atlas_values))
        out_labels = []
        out_values = []
        # Iterate over the parcels (existing)
        for t_v in atlas_roi_vals:
            t_values = agg_func(data[:, atlas_values == t_v], axis=-1)
            out_values.append(t_values)
            # Update the labels just in case a parcel has no voxels
            # in it
            out_labels.append(t_labels[t_v - 1])

        out_values = np.array(out_values).T
        out = {"data": out_values, "columns": out_labels}
        if out_values.shape[0] > 1:
            out["row_names"] = "scan"
        return out
