"""Provide class for ALFF / fALFF on parcels."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Kaustubh R. Patil <k.patil@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Any, Dict, List, Optional, Union

from ...api.decorators import register_marker
from ...utils import logger
from ..parcel_aggregation import ParcelAggregation
from .falff_base import ALFFBase


@register_marker
class ALFFParcels(ALFFBase):
    """Class for ALFF / fALFF on parcels.

    Parameters
    ----------
    parcellation : str or list of str
        The name(s) of the parcellation(s). Check valid options by calling
        :func:`.list_parcellations`.
    fractional : bool
        Whether to compute fractional ALFF.
    using : {"junifer", "afni"}
        Implementation to use for computing ALFF:

        * "junifer" : Use ``junifer``'s own ALFF implementation
        * "afni" : Use AFNI's ``3dRSFC``

    highpass : positive float, optional
        The highpass cutoff frequency for the bandpass filter. If 0,
        it will not apply a highpass filter (default 0.01).
    lowpass : positive float, optional
        The lowpass cutoff frequency for the bandpass filter (default 0.1).
    tr : positive float, optional
        The Repetition Time of the BOLD data. If None, will extract
        the TR from NIfTI header (default None).
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

    Notes
    -----
    The ``tr`` parameter is crucial for the correctness of fALFF/ALFF
    computation. If a dataset is correctly preprocessed, the ``tr`` should be
    extracted from the NIfTI without any issue. However, it has been
    reported that some preprocessed data might not have the correct ``tr`` in
    the NIfTI header.

    ALFF/fALFF are computed using a bandpass butterworth filter. See
    :func:`scipy.signal.butter` and :func:`scipy.signal.filtfilt` for more
    details.

    """

    def __init__(
        self,
        parcellation: Union[str, List[str]],
        fractional: bool,
        using: str,
        highpass: float = 0.01,
        lowpass: float = 0.1,
        tr: Optional[float] = None,
        agg_method: str = "mean",
        agg_method_params: Optional[Dict] = None,
        masks: Union[str, Dict, List[Union[Dict, str]], None] = None,
        name: Optional[str] = None,
    ) -> None:
        # Superclass init first to validate `using` parameter
        super().__init__(
            fractional=fractional,
            highpass=highpass,
            lowpass=lowpass,
            using=using,
            tr=tr,
            name=name,
        )
        self.parcellation = parcellation
        self.agg_method = agg_method
        self.agg_method_params = agg_method_params
        self.masks = masks

    def compute(
        self,
        input: Dict[str, Any],
        extra_input: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Compute.

        Parameters
        ----------
        input : dict
            The BOLD data as dictionary.
        extra_input : dict, optional
            The other fields in the pipeline data object (default None).

        Returns
        -------
        dict
            The computed result as dictionary. The dictionary has the following
            keys:

            * ``data`` : the actual computed values as a numpy.ndarray
            * ``col_names`` : the column labels for the computed values as list

        """
        logger.info("Calculating ALFF / fALFF for parcels")

        # Compute ALFF / fALFF
        output_data, output_file_path = self._compute(input_data=input)

        # Initialize parcel aggregation
        parcel_aggregation = ParcelAggregation(
            parcellation=self.parcellation,
            method=self.agg_method,
            method_params=self.agg_method_params,
            masks=self.masks,
            on="BOLD",
        )
        # Perform aggregation on ALFF / fALFF
        parcel_aggregation_input = dict(input.items())
        parcel_aggregation_input["data"] = output_data
        parcel_aggregation_input["path"] = output_file_path
        output = parcel_aggregation.compute(
            input=parcel_aggregation_input,
            extra_input=extra_input,
        )

        return output
