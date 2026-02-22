"""Provide class for parcel aggregation."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Any, ClassVar, Literal, Optional, Union

import numpy as np
from nilearn.image import math_img
from nilearn.maskers import NiftiMasker

from ..api.decorators import register_marker
from ..data import get_data
from ..datagrabber import DataType
from ..stats import get_aggfunc_by_name
from ..storage import StorageType
from ..typing import Dependencies, MarkerInOutMappings
from ..utils import raise_error, warn_with_log
from .base import BaseMarker, logger


__all__ = ["ParcelAggregation"]


@register_marker
class ParcelAggregation(BaseMarker):
    """Class for parcel aggregation.

    Parameters
    ----------
    parcellation : list of str
        The name(s) of the parcellation(s) to use.
        See :func:`.list_data` for options.
    method : str, optional
        The aggregation function to use.
        See :func:`.get_aggfunc_by_name` for options
        (default "mean").
    method_params : dict or None, optional
        The parameters to pass to the aggregation function.
        See :func:`.get_aggfunc_by_name` for options (default None).
    time_method : str or None, optional
        The aggregation function to use for time series after applying
        :term:`method` (only applicable to BOLD data). If None,
        it will not operate on the time dimension (default None).
    time_method_params : dict or None, optional
        The parameters to pass to the time aggregation function (default None).
    on : list of {``DataType.T1w``, ``DataType.T2w``, ``DataType.BOLD``, \
         ``DataType.VBM_GM``, ``DataType.VBM_WM``, ``DataType.VBM_CSF``, \
         ``DataType.FALFF``, ``DataType.GCOR``, ``DataType.LCOR``} or None, \
         optional
        The data type(s) to apply the marker on.
        If None, will work on all available data.
        Check :enum:`.DataType` for valid values (default None).
    masks : list of dict or str, or None, optional
        The specification of the masks to apply to regions before extracting
        signals. Check :ref:`Using Masks <using_masks>` for more details.
        If None, will not apply any mask (default None).
    name : str or None, optional
        The name of the marker.
        If None, will use the class name (default None).

    Raises
    ------
    ValueError
        If ``time_method`` is specified for non-BOLD data or if
        ``time_method_params`` is not None when ``time_method`` is None.

    """

    _DEPENDENCIES: ClassVar[Dependencies] = {"nilearn", "numpy"}

    _MARKER_INOUT_MAPPINGS: ClassVar[MarkerInOutMappings] = {
        DataType.T1w: {
            "aggregation": StorageType.Vector,
        },
        DataType.T2w: {
            "aggregation": StorageType.Vector,
        },
        DataType.BOLD: {
            "aggregation": StorageType.Timeseries,
        },
        DataType.VBM_GM: {
            "aggregation": StorageType.Vector,
        },
        DataType.VBM_WM: {
            "aggregation": StorageType.Vector,
        },
        DataType.VBM_CSF: {
            "aggregation": StorageType.Vector,
        },
        DataType.FALFF: {
            "aggregation": StorageType.Vector,
        },
        DataType.GCOR: {
            "aggregation": StorageType.Vector,
        },
        DataType.LCOR: {
            "aggregation": StorageType.Vector,
        },
    }

    parcellation: list[str]
    method: str = "mean"
    method_params: Optional[dict[str, Any]] = None
    time_method: Optional[str] = None
    time_method_params: Optional[dict[str, Any]] = None
    masks: Optional[list[Union[dict, str]]] = None
    on: Optional[
        list[
            Literal[
                DataType.T1w,
                DataType.T2w,
                DataType.BOLD,
                DataType.VBM_GM,
                DataType.VBM_WM,
                DataType.VBM_CSF,
                DataType.FALFF,
                DataType.GCOR,
                DataType.LCOR,
            ]
        ]
    ] = None

    def validate_marker_params(self) -> None:
        """Run extra logical validation for marker."""
        # self.on is set already
        if "BOLD" not in self.on and self.time_method is not None:
            raise_error(
                "`time_method` can only be used with BOLD data. "
                "Please remove `time_method` parameter."
            )
        if self.time_method is None and self.time_method_params is not None:
            raise_error(
                "`time_method_params` can only be used with `time_method`. "
                "Please remove `time_method_params` parameter."
            )

    def compute(
        self, input: dict[str, Any], extra_input: Optional[dict] = None
    ) -> dict:
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

            * ``aggregation`` : dictionary with the following keys:

                - ``data`` : ROI values as ``numpy.ndarray``
                - ``col_names`` : ROI labels as list of str

        Warns
        -----
        RuntimeWarning
            If time aggregation is required but only time point is available.

        """
        t_input_img = input["data"]
        logger.debug(f"Parcel aggregation using {self.method}")
        # Get aggregation function
        agg_func = get_aggfunc_by_name(
            name=self.method, func_params=self.method_params
        )

        # Get parcellation tailored to target image
        parcellation_img, labels = get_data(
            kind="parcellation",
            names=self.parcellation,
            target_data=input,
            extra_input=extra_input,
        )

        # Get binarized parcellation image for masking
        parcellation_bin = math_img(
            "np.squeeze(img) != 0", img=parcellation_img
        )

        # Load mask
        if self.masks is not None:
            logger.debug(f"Masking with {self.masks}")
            # Get tailored mask
            mask_img = get_data(
                kind="mask",
                names=self.masks,
                target_data=input,
                extra_input=extra_input,
            )
            # Get "logical and" version of parcellation and mask
            parcellation_bin = math_img(
                "np.logical_and(img, np.squeeze(mask))",
                img=parcellation_bin,
                mask=mask_img,
            )

        # Initialize masker
        logger.debug("Masking")
        masker = NiftiMasker(
            parcellation_bin, target_affine=t_input_img.affine
        )
        # Mask the input data and the parcellation
        data = masker.fit_transform(t_input_img)
        parcellation_values = np.squeeze(
            masker.transform(parcellation_img)
        ).astype(int)

        # Get the values for each parcel and apply agg function
        logger.debug("Computing ROI means")
        out_values = []
        # Iterate over the parcels (existing)
        for t_v in labels.keys():
            t_values = agg_func(data[:, parcellation_values == t_v], axis=-1)
            out_values.append(t_values)
            # Update the labels just in case a parcel has no voxels
            # in it

        out_values = np.array(out_values).T

        # Apply time dimension aggregation if required
        if self.time_method is not None:
            if out_values.shape[0] > 1:
                logger.debug("Aggregating time dimension")
                time_agg_func = get_aggfunc_by_name(
                    self.time_method, func_params=self.time_method_params
                )
                out_values = time_agg_func(out_values, axis=0)
            else:
                warn_with_log(
                    "No time dimension to aggregate as only one time point is "
                    "available."
                )
        # Format the output
        return {
            "aggregation": {
                "data": out_values,
                "col_names": list(labels.values()),
            },
        }
