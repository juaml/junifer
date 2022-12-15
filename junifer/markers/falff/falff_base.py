"""Provide abstract class for computing fALFF."""
# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Kaustubh R. Patil <k.patil@fz-juelich.de>
# License: AGPL

from typing import TYPE_CHECKING, Dict, List, Optional, Tuple


from ..base import BaseMarker
from .falff_estimator import AmplitudeLowFrequencyFluctuationEstimator
from ...utils.logging import raise_error, warn_with_log


class AmplitudeLowFrequencyFluctuationBase(BaseMarker):
    """Base class for (fractional) Amplitude Low Frequency Fluctuation.

    Parameters
    ----------
    fractional : bool
        Whether to compute fractional ALFF.
    highpass : float
        Highpass cutoff frequency.
    lowpass : float
        Lowpass cutoff frequency.
    order : int
        Order of the filter.
    tr : float, optional
        The Repetition Time of the BOLD data. If None, will extract
        the TR from NIFTI header (default None).
    use_afni : bool, optional
        Whether to use AFNI for computing. If None, will use AFNI only
        if available (default None).
    name : str, optional
        The name of the marker. If None, it will use the class name
        (default None).
    Notes
    -----
        The `tr` parameter is crucial for the correctness of fALFF/ALFF
        computation. If a dataset is correctly preprocessed, the TR should be
        extracted from the NIFTI without any issue. However, it has been
        reported that some preprocessed data might not have the correct TR in
        the NIFTI header.

    """

    _EXT_DEPENDENCIES = [
        {
            "name": "afni",
            "optional": True,
            "commands": ["3dRSFC", "3dAFNItoNIFTI"],
        },
    ]

    def __init__(
        self,
        fractional: bool,
        highpass: float,
        lowpass: float,
        order: int,
        tr: Optional[float] = None,
        use_afni: Optional[bool] = None,
        name: Optional[str] = None,
    ) -> None:
        if highpass <= 0:
            raise_error("Highpass must be positive")
        if lowpass <= 0:
            raise_error("Lowpass must be positive")
        if highpass >= lowpass:
            raise_error("Highpass must be lower than lowpass")
        self.highpass = highpass
        self.lowpass = lowpass
        if order <= 0 and use_afni is False:
            raise_error("Order must be positive")
        self.order = order
        self.tr = tr
        self.use_afni = use_afni
        self.fractional = fractional

        # Create a name based on the class name if none is provided
        if name is None:
            suffix = "_fractional" if fractional else ""
            name = f"{self.__class__.__name__}{suffix}"
        super().__init__(on="BOLD", name=name)

    def validate(self, input: List[str]) -> List[str]:
        """Validate the the pipeline step.

        Parameters
        ----------
        input : list of str
            The input to the pipeline step.

        Returns
        -------
        list of str
            The output of the pipeline step.

        Raises
        ------
        ValueError
            If the pipeline step object is missing dependencies required for
            its working, if the input does not have the required data, or
            if AFNI was not used and the order is not positive.

        Warns
        -----
        UserWarning
            If AFNI is used and the order is not 0.
        """
        out = super().validate(input)
        if self.use_afni is True and self.order > 0:
            warn_with_log(
                "AFNI will not consider the order of the filter. Set this "
                "parameter to 0 to avoid this warning.")
        elif self.use_afni is False and self.order <= 0:
            raise_error(
                "Order must be positive if AFNI is not used.")
        return out

    def get_valid_inputs(self) -> List[str]:
        """Get valid data types for input.

        Returns
        -------
        list of str
            The list of data types that can be used as input for this marker.

        """
        valid = ["BOLD"]
        return valid

    def get_output_type(self, input: List[str]) -> List[str]:
        """Get output type.

        Parameters
        ----------
        input : list of str
            The type of data to work on.

        Returns
        -------
        list of str
            The list of storage types.

        """
        return ["table"]

    def compute(
        self,
        input: Dict[str, Dict],
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
        estimator = AmplitudeLowFrequencyFluctuationEstimator(
            use_afni=self.use_afni
        )

        alff, falff = estimator.fit_transform(
            input_data=input,
            highpass=self.highpass,
            lowpass=self.lowpass,
            order=self.order,
            tr=self.tr,
        )
        post_data = falff if self.fractional else alff

        post_input = {
            'data': post_data,
            'path': None,
        }

        out = self._postprocess(post_input)

        return out
