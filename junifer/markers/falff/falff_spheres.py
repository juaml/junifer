"""Provide class for ALFF / fALFF on spheres."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Kaustubh R. Patil <k.patil@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Any, Dict, List, Optional, Union

from ...api.decorators import register_marker
from ...utils import logger
from ..sphere_aggregation import SphereAggregation
from .falff_base import ALFFBase


@register_marker
class ALFFSpheres(ALFFBase):
    """Class for computing ALFF / fALFF on spheres.

    Parameters
    ----------
    coords : str
        The name of the coordinates list to use. See
        :func:`.list_coordinates` for options.
    fractional : bool
        Whether to compute fractional ALFF.
    using : {"junifer", "afni"}
        Implementation to use for computing ALFF:

        * "junifer" : Use ``junifer``'s own ALFF implementation
        * "afni" : Use AFNI's ``3dRSFC``

    radius : float, optional
        The radius of the sphere in mm. If None, the signal will be extracted
        from a single voxel. See :class:`nilearn.maskers.NiftiSpheresMasker`
        for more information (default None).
    allow_overlap : bool, optional
        Whether to allow overlapping spheres. If False, an error is raised if
        the spheres overlap (default is False).
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
        :func:`.get_aggfunc_by_name`.
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
    the NIFTI header.

    ALFF/fALFF are computed using a bandpass butterworth filter. See
    :func:`scipy.signal.butter` and :func:`scipy.signal.filtfilt` for more
    details.

    """

    def __init__(
        self,
        coords: str,
        fractional: bool,
        using: str,
        radius: Optional[float] = None,
        allow_overlap: bool = False,
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
        self.coords = coords
        self.radius = radius
        self.allow_overlap = allow_overlap
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
        logger.info("Calculating ALFF / fALFF for spheres")

        # Compute ALFF / fALFF
        output_data, output_file_path = self._compute(input_data=input)

        # Initialize sphere aggregation
        sphere_aggregation = SphereAggregation(
            coords=self.coords,
            radius=self.radius,
            allow_overlap=self.allow_overlap,
            method=self.agg_method,
            method_params=self.agg_method_params,
            masks=self.masks,
            on="BOLD",
        )
        # Perform aggregation on ALFF / fALFF
        sphere_aggregation_input = dict(input.items())
        sphere_aggregation_input["data"] = output_data
        sphere_aggregation_input["path"] = output_file_path
        output = sphere_aggregation.compute(
            input=sphere_aggregation_input,
            extra_input=extra_input,
        )

        return output
