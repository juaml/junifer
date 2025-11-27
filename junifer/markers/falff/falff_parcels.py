"""Provide class for ALFF / fALFF on parcels."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Kaustubh R. Patil <k.patil@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Annotated, Any, Literal, Optional, Union

from pydantic import BeforeValidator

from ...api.decorators import register_marker
from ...datagrabber import DataType
from ...utils import logger
from ..parcel_aggregation import ParcelAggregation
from ..utils import _ensure_list
from .falff_base import ALFFBase


__all__ = ["ALFFParcels"]


@register_marker
class ALFFParcels(ALFFBase):
    """Class for ALFF / fALFF on parcels.

    Parameters
    ----------
    parcellation : str or list of str
        The name(s) of the parcellation(s) to use.
        See :func:`.list_data` for options.
    using : :enum:`.ALFFImpl`
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
    masks : list of dict or str, or None, optional
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
    the NIfTI header.

    ALFF/fALFF are computed using a bandpass butterworth filter. See
    :func:`scipy.signal.butter` and :func:`scipy.signal.filtfilt` for more
    details.

    """

    parcellation: Annotated[
        Union[str, list[str]], BeforeValidator(_ensure_list)
    ]
    on: list[Literal[DataType.BOLD]] = [DataType.BOLD]  # noqa: RUF012

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
        logger.info("Calculating ALFF / fALFF for parcels")

        # Compute ALFF + fALFF
        alff_output, falff_output, alff_output_path, falff_output_path = (
            self._compute(input_data=input)
        )

        # Perform aggregation on ALFF + fALFF
        aggregation_alff_input = dict(input.items())
        aggregation_falff_input = dict(input.items())
        aggregation_alff_input["data"] = alff_output
        aggregation_falff_input["data"] = falff_output
        aggregation_alff_input["path"] = alff_output_path
        aggregation_falff_input["path"] = falff_output_path

        return {
            "alff": {
                **ParcelAggregation(
                    parcellation=self.parcellation,
                    method=self.agg_method,
                    method_params=self.agg_method_params,
                    masks=self.masks,
                    on=[DataType.BOLD],
                ).compute(
                    input=aggregation_alff_input,
                    extra_input=extra_input,
                )["aggregation"],
            },
            "falff": {
                **ParcelAggregation(
                    parcellation=self.parcellation,
                    method=self.agg_method,
                    method_params=self.agg_method_params,
                    masks=self.masks,
                    on=[DataType.BOLD],
                ).compute(
                    input=aggregation_falff_input,
                    extra_input=extra_input,
                )["aggregation"],
            },
        }
