"""Provide class for computing fALFF on spheres."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Kaustubh R. Patil <k.patil@fz-juelich.de>
# License: AGPL

from typing import Dict, Optional

from ...api.decorators import register_marker
from .. import SphereAggregation
from .falff_base import AmplitudeLowFrequencyFluctuationBase


@register_marker
class AmplitudeLowFrequencyFluctuationSpheres(
    AmplitudeLowFrequencyFluctuationBase
):
    """Class for computing fALFF/ALFF on spheres.

    Parameters
    ----------
    coords : str
        The name of the coordinates list to use. See
        :func:`junifer.data.coordinates.list_coordinates` for options.
    radius : float, optional
        The radius of the sphere in mm. If None, the signal will be extracted
        from a single voxel. See :class:`nilearn.maskers.NiftiSpheresMasker`
        for more information (default None).
    fractional : bool
        Whether to compute fractional ALFF.
    highpass : positive float, optional
        The highpass cutoff frequency for the bandpass filter (default 0.01).
    lowpass : positive float, optional
        The lowpass cutoff frequency for the bandpass filter (default 0.1).
    tr : positive float, optional
        The Repetition Time of the BOLD data. If None, will extract
        the TR from NIFTI header (default None).
    use_afni : bool, optional
        Whether to use AFNI for computing. If None, will use AFNI only
        if available (default None).
    mask : str, optional
        The name of the mask to apply to regions before extracting signals.
        Check valid options by calling :func:`junifer.data.masks.list_masks`
        (default None).
    method : str, optional
        The method to perform aggregation using. Check valid options in
        :func:`junifer.stats.get_aggfunc_by_name` (default "mean").
    method_params : dict, optional
        Parameters to pass to the aggregation function. Check valid options in
        :func:`junifer.stats.get_aggfunc_by_name`.
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
        coords: str,
        fractional: bool,
        radius: Optional[float] = None,
        highpass: float = 0.01,
        lowpass: float = 0.1,
        tr: Optional[float] = None,
        use_afni: Optional[bool] = None,
        mask: Optional[str] = None,
        method: str = "mean",
        method_params: Optional[Dict] = None,
        name: Optional[str] = None,
    ) -> None:
        self.coords = coords
        self.radius = radius
        self.mask = mask
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

    def _postprocess(self, input: Dict) -> Dict:
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
            * ``columns`` : the column labels for the computed values as a list

        """
        pa = SphereAggregation(
            coords=self.coords,
            radius=self.radius,
            method=self.method,
            method_params=self.method_params,
            mask=self.mask,
            on="fALFF",
        )

        # get the 2D timeseries after parcel aggregation
        out = pa.compute(input)

        return out
