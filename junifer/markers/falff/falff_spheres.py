"""Provide class for ALFF / fALFF on spheres."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Kaustubh R. Patil <k.patil@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Any, Literal, Optional, Union

from pydantic import PositiveFloat

from ...api.decorators import register_marker
from ...datagrabber import DataType
from ...utils import logger
from ..sphere_aggregation import SphereAggregation
from .falff_base import ALFFBase


__all__ = ["ALFFSpheres"]


@register_marker
class ALFFSpheres(ALFFBase):
    """Class for computing ALFF / fALFF on spheres.

    Parameters
    ----------
    coords : str
        The name of the coordinates list to use.
        See :func:`.list_data` for options.
    using : :enum:`.ALFFImpl`
    radius : ``zero`` or positive float or None, optional
        The radius of the sphere in millimetres.
        If None, the signal will be extracted from a single voxel.
        See :class:`.JuniferNiftiSpheresMasker` for more information
        (default None).
    allow_overlap : bool, optional
        Whether to allow overlapping spheres.
        If False, an error is raised if the spheres overlap (default False).
    agg_method : str, optional
        The aggregation function to use.
        See :func:`.get_aggfunc_by_name` for options (default "mean").
    agg_method_params : dict or None, optional
        The parameters to pass to the aggregation function.
        See :func:`.get_aggfunc_by_name` for valid options (default None).
    highpass : positive float, optional
        Highpass cutoff frequency (default 0.01).
    lowpass : positive float, optional
        Lowpass cutoff frequency (default 0.1).
    tr : positive float, optional
        The repetition time of the BOLD data.
        If None, will extract the TR from NIfTI header (default None).
    masks : str, dict, list of them or None, optional
        The specification of the masks to apply to regions before extracting
        signals. Check :ref:`Using Masks <using_masks>` for more details.
        If None, will not apply any mask (default None).
    name : str or None, optional
        The name of the marker.
        If None, will use the class name (default None).

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

    coords: str
    radius: Optional[Union[Literal[0], PositiveFloat]] = None
    allow_overlap: bool = False

    def compute(
        self,
        input: dict[str, Any],
        extra_input: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
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
            The computed result as dictionary. This will be either returned
            to the user or stored in the storage by calling the store method
            with this as a parameter. The dictionary has the following keys:

            * ``alff`` : dictionary with the following keys:

              - ``data`` : ROI values as ``numpy.ndarray``
              - ``col_names`` : ROI labels as list of str

            * ``falff`` : dictionary with the following keys:

              - ``data`` : ROI values as ``numpy.ndarray``
              - ``col_names`` : ROI labels as list of str

        """
        logger.info("Calculating ALFF / fALFF for spheres")

        # Compute ALFF + fALFF
        alff_output, falff_output, alff_output_path, falff_output_path = (
            self._compute(input_data=input)
        )

        # Perform aggregation on ALFF / fALFF
        aggregation_alff_input = dict(input.items())
        aggregation_falff_input = dict(input.items())
        aggregation_alff_input["data"] = alff_output
        aggregation_falff_input["data"] = falff_output
        aggregation_alff_input["path"] = alff_output_path
        aggregation_falff_input["path"] = falff_output_path

        return {
            "alff": {
                **SphereAggregation(
                    coords=self.coords,
                    radius=self.radius,
                    allow_overlap=self.allow_overlap,
                    method=self.agg_method,
                    method_params=self.agg_method_params,
                    masks=self.masks,
                    on=DataType.BOLD,
                ).compute(
                    input=aggregation_alff_input,
                    extra_input=extra_input,
                )["aggregation"],
            },
            "falff": {
                **SphereAggregation(
                    coords=self.coords,
                    radius=self.radius,
                    allow_overlap=self.allow_overlap,
                    method=self.agg_method,
                    method_params=self.agg_method_params,
                    masks=self.masks,
                    on=DataType.BOLD,
                ).compute(
                    input=aggregation_falff_input,
                    extra_input=extra_input,
                )["aggregation"],
            },
        }
