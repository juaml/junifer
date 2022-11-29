"""Provide class for parcel aggregation."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Any, Dict, List, Optional, Union

import numpy as np
from nilearn.image import math_img, new_img_like, resample_to_img
from nilearn.maskers import NiftiMasker

from ..api.decorators import register_marker
from ..data import load_mask, load_parcellation
from ..stats import get_aggfunc_by_name
from ..utils import logger
from .base import BaseMarker


@register_marker
class ParcelAggregation(BaseMarker):
    """Class for parcel aggregation.

    Parameters
    ----------
    parcellation : str or list of str
        The name(s) of the parcellation(s). Check valid options by calling
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

    _DEPENDENCIES = {"nilearn", "numpy"}

    def __init__(
        self,
        parcellation: Union[str, List[str]],
        method: str,
        method_params: Optional[Dict[str, Any]] = None,
        mask: Optional[str] = None,
        on: Union[List[str], str, None] = None,
        name: Optional[str] = None,
    ) -> None:
        if not isinstance(parcellation, list):
            parcellation = [parcellation]
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

        if input_type in ["VBM_GM", "VBM_WM", "fALFF", "GCOR", "LCOR"]:
            return "table"
        elif input_type == "BOLD":
            return "timeseries"
        else:
            raise ValueError(f"Unknown input kind for {input_type}")

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

        # Load the parcellations
        all_parcelations = []
        all_labels = []
        for t_parc_name in self.parcellation:
            t_parcellation, t_labels, _ = load_parcellation(
                name=t_parc_name,
                resolution=resolution,
            )
            # Resample all of them to the image
            t_parcellation_img_res = resample_to_img(
                t_parcellation,
                t_input,
                interpolation="nearest",
                copy=True,
            )
            all_parcelations.append(t_parcellation_img_res)
            all_labels.append(t_labels)

        # Avoid merging if there is only one parcellation
        if len(all_parcelations) == 1:
            parcellation_img_res = all_parcelations[0]
            labels = all_labels[0]
        else:
            # Merge the parcellations
            parc_data = all_parcelations[0].get_fdata()
            labels = all_labels[0]
            for t_parc, t_labels in zip(all_parcelations[1:], all_labels[1:]):
                # Get the data from this parcellation
                t_parc_data = t_parc.get_fdata().copy()  # must be copied
                # Increase the values of each ROI to match the labels
                t_parc_data[t_parc_data != 0] += len(labels)

                # Only set new values for the voxels that are 0
                # This makes sure that the voxels that are in multiple
                # parcellations are assigned to the parcellation that was
                # first in the list.
                parc_data[parc_data == 0] += t_parc_data[parc_data == 0]
                labels.extend(t_labels)

            parcellation_img_res = new_img_like(
                all_parcelations[0],
                parc_data,
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
            out_labels.append(labels[t_v - 1])

        out_values = np.array(out_values).T
        out = {"data": out_values, "columns": out_labels}
        return out
