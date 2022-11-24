"""Provide class for computing fALFF on parcels."""
# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Kaustubh R. Patil <k.patil@fz-juelich.de>
# License: AGPL

from typing import Dict, List, Optional, Union, Tuple


from ...api.decorators import register_marker
from .falff_base import AmplitudeLowFrequencyFluctuationBase
from .. import ParcelAggregation


@register_marker
class AmplitudeLowFrequencyFluctuationParcels(
    AmplitudeLowFrequencyFluctuationBase
):
    """Class for computing fALFF/ALFF on parcels.

    Parameters
    ----------
    parcellation : str or list of str
        The name(s) of the parcellation(s). Check valid options by calling
        :func:`junifer.data.parcellations.list_parcellations`.
    highpass : float
        The highpass cutoff frequency for the bandpass filter.
    lowpass : float
        The lowpass cutoff frequency for the bandpass filter.
    order : int
        The order of the bandpass filter.
    mask : str, optional
        The name of the mask to apply to regions before extracting signals.
        Check valid options by calling :func:`junifer.data.masks.list_masks`
        (default None).
    tr : float, optional
        The Repetition Time of the BOLD data. If None, will extract
        the TR from NIFTI header (default None).
    name : str, optional
        The name of the marker. If None, will use the class name (default
        None).

    Notes
    -----
    The `tr` parameter is crucial for the correctness of fALFF/ALFF
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
        highpass: float,
        lowpass: float,
        order: int,
        mask: Optional[str] = None,
        tr: Optional[float] = None,
        name: Optional[str] = None,
    ) -> None:
        self.parcellation = parcellation
        self.mask = mask

        super().__init__(
            highpass=highpass,
            lowpass=lowpass,
            order=order,
            tr=tr,
            name=name,
        )

    def compute(self, input: Dict) -> Tuple[Dict, Dict]:
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
        alff: dict
            The computed ALFF as dictionary. The dictionary has the following
            keys:

            * ``data`` : the actual computed values as a numpy.ndarray
            * ``columns`` : the column labels for the computed values as a list

        falff: dict
            The computed fALFF as dictionary. The dictionary has the following
            keys:

            * ``data`` : the actual computed values as a numpy.ndarray
            * ``columns`` : the column labels for the computed values as a list
        """
        pa = ParcelAggregation(
            parcellation=self.parcellation,
            method="mean",
            mask=self.mask,
            on="BOLD",
        )

        # get the 2D timeseries after parcel aggregation
        parcels = pa.compute(input)
        timeseries = parcels["data"]
        labels = parcels["columns"]
        tr = self.tr or input["BOLD"].header["pixdim"][4]

        out = super().compute_falff(timeseries, labels, tr)
        return out
