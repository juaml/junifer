"""Provide class for computing fALFF on parcels."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Kaustubh R. Patil <k.patil@fz-juelich.de>
# License: AGPL

from typing import Dict, List, Optional, Union

from ...api.decorators import register_marker
from .. import ParcelAggregation
from .falff_base import ALFFBase


@register_marker
class ALFFParcels(ALFFBase):
    """Class for computing fALFF/ALFF on parcels.

    Parameters
    ----------
    parcellation : str or list of str
        The name(s) of the parcellation(s). Check valid options by calling
        :func:`.list_parcellations`.
    fractional : bool
        Whether to compute fractional ALFF.
    highpass : positive float, optional
        The highpass cutoff frequency for the bandpass filter. If 0,
        it will not apply a highpass filter (default 0.01).
    lowpass : positive float, optional
        The lowpass cutoff frequency for the bandpass filter (default 0.1).
    tr : positive float, optional
        The Repetition Time of the BOLD data. If None, will extract
        the TR from NIFTI header (default None).
    use_afni : bool, optional
        Whether to use AFNI for computing. If None, will use AFNI only
        if available (default None).
    masks : str, dict or list of dict or str, optional
        The specification of the masks to apply to regions before extracting
        signals. Check :ref:`Using Masks <using_masks>` for more details.
        If None, will not apply any mask (default None).
    method : str, optional
        The method to perform aggregation using. Check valid options in
        :func:`.get_aggfunc_by_name` (default "mean").
    method_params : dict, optional
        Parameters to pass to the aggregation function. Check valid options in
        :func:`.get_aggfunc_by_name`.
    name : str, optional
        The name of the marker. If None, will use the class name (default
        None).

    Notes
    -----
    The ``tr`` parameter is crucial for the correctness of fALFF/ALFF
    computation. If a dataset is correctly preprocessed, the TR should be
    extracted from the NIFTI without any issue. However, it has been
    reported that some preprocessed data might not have the correct TR in
    the NIFTI header.

    ALFF/fALFF are computed using a bandpass butterworth filter. See
    :func:`scipy.signal.butter` and :func:`scipy.signal.filtfilt` for more
    details.
    """

    def __init__(
        self,
        parcellation: Union[str, List[str]],
        fractional: bool,
        highpass: float = 0.01,
        lowpass: float = 0.1,
        tr: Optional[float] = None,
        use_afni: Optional[bool] = None,
        masks: Union[str, Dict, List[Union[Dict, str]], None] = None,
        method: str = "mean",
        method_params: Optional[Dict] = None,
        name: Optional[str] = None,
    ) -> None:
        self.parcellation = parcellation
        self.masks = masks
        self.method = method
        self.method_params = method_params
        super().__init__(
            fractional=fractional,
            highpass=highpass,
            lowpass=lowpass,
            tr=tr,
            name=name,
            use_afni=use_afni,
        )

    def _postprocess(
        self, input: Dict, extra_input: Optional[Dict] = None
    ) -> Dict:
        """Compute ALFF and fALFF.

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
            The computed ALFF as dictionary. The dictionary has the following
            keys:

            * ``data`` : the actual computed values as a numpy.ndarray
            * ``col_names`` : the column labels for the computed values as list

        """
        pa = ParcelAggregation(
            parcellation=self.parcellation,
            method=self.method,
            method_params=self.method_params,
            masks=self.masks,
            on="fALFF",
        )

        # get the 2D timeseries after parcel aggregation
        out = pa.compute(input, extra_input=extra_input)

        return out
