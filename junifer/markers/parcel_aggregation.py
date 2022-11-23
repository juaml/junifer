"""Provide class for parcel aggregation."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

import numpy as np
from nilearn.image import math_img, resample_to_img
from nilearn.maskers import NiftiMasker

from ..api.decorators import register_marker
from ..data import load_parcellation, load_mask
from ..stats import get_aggfunc_by_name
from ..utils import logger
from .base import BaseMarker

if TYPE_CHECKING:
    from junifer.storage import BaseFeatureStorage


@register_marker
class ParcelAggregation(BaseMarker):
    """Class for parcel aggregation.

    Parameters
    ----------
    parcellation : str
        The name of the parcellation. Check valid options by calling
        :func:`junifer.data.parcellations.list_parcellations`.
    method : str
        The method to perform aggregation using. Check valid options in
        :func:`junifer.stats.get_aggfunc_by_name`.
    method_params : dict, optional
        Parameters to pass to the aggregation function. Check valid options in
        :func:`junifer.stats.get_aggfunc_by_name`.
    mask : str, optional
        The name of the mask to apply to regions before extracting signals.
        Check valid options by calling :func:`junifer.data.masks.list_masks`
        (default None).
    on : {"T1w", "BOLD", "VBM_GM", "VBM_WM", "fALFF", "GCOR", "LCOR"} \
         or list of the options, optional
        The data types to apply the marker to. If None, will work on all
        available data (default None).
    name : str, optional
        The name of the marker. If None, will use the class name (default
        None).
    """

    def __init__(
        self,
        parcellation: str,
        method: str,
        method_params: Optional[Dict[str, Any]] = None,
        mask: Optional[str] = None,
        on: Union[List[str], str, None] = None,
        name: Optional[str] = None,
    ) -> None:
        self.parcellation = parcellation
        self.method = method
        self.method_params = method_params or {}
        self.mask = mask
        super().__init__(on=on, name=name)

    def get_valid_inputs(self) -> List[str]:
        """Get valid data types for input.

        Returns
        -------
        list of str
            The list of data types that can be used as input for this marker.

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
            The list of storage kinds.

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

            * ``data`` : the actual computed values as a numpy.ndarray
            * ``columns`` : the column labels for the computed values as a list
            * ``row_names`` (if more than one row is present in data): "scan"

        """
        t_input = input["data"]
        logger.debug(f"Parcel aggregation using {self.method}")
        agg_func = get_aggfunc_by_name(
            name=self.method,
            func_params=self.method_params,
        )
        # Get the min of the voxels sizes and use it as the resolution
        resolution = np.min(t_input.header.get_zooms()[:3])
        t_parcellation, t_labels, _ = load_parcellation(
            name=self.parcellation,
            resolution=resolution,
        )

        parcellation_img_res = resample_to_img(
            t_parcellation,
            t_input,
            interpolation="nearest",
            copy=True,
        )

        parcellation_bin = math_img(
            "img != 0",
            img=parcellation_img_res,
        )

        if self.mask is not None:
            logger.debug(f"Masking with {self.mask}")
            mask_img, _ = load_mask(name=self.mask, resolution=resolution)
            mask_img = resample_to_img(
                mask_img,
                t_input,
                interpolation="nearest",
                copy=True,
            )
            parcellation_bin = math_img(
                "np.logical_and(img, mask)",
                img=parcellation_bin,
                mask=mask_img,
            )

        logger.debug("Masking")
        masker = NiftiMasker(
            parcellation_bin, target_affine=t_input.affine
        )  # type: ignore

        # Mask the input data and the parcellation
        data = masker.fit_transform(t_input)
        parcellation_values = masker.transform(parcellation_img_res)
        parcellation_values = np.squeeze(parcellation_values).astype(int)

        # Get the values for each parcel and apply agg function
        logger.debug("Computing ROI means")
        parcellation_roi_vals = sorted(np.unique(parcellation_values))
        out_labels = []
        out_values = []
        # Iterate over the parcels (existing)
        for t_v in parcellation_roi_vals:
            t_values = agg_func(data[:, parcellation_values == t_v], axis=-1)
            out_values.append(t_values)
            # Update the labels just in case a parcel has no voxels
            # in it
            out_labels.append(t_labels[t_v - 1])

        out_values = np.array(out_values).T
        out = {"data": out_values, "columns": out_labels}
        if out_values.shape[0] > 1:
            out["row_names"] = "scan"
        return out
