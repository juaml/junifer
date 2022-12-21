"""Provide abstract class for computing fALFF."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Kaustubh R. Patil <k.patil@fz-juelich.de>
# License: AGPL

from abc import abstractmethod
from typing import Dict, List, Optional

from ...utils.logging import raise_error
from ..base import BaseMarker
from .falff_estimator import AmplitudeLowFrequencyFluctuationEstimator


class AmplitudeLowFrequencyFluctuationBase(BaseMarker):
    """Base class for (fractional) Amplitude Low Frequency Fluctuation.

    Parameters
    ----------
    fractional : bool
        Whether to compute fractional ALFF.
    highpass : positive float
        Highpass cutoff frequency.
    lowpass : positive float
        Lowpass cutoff frequency.
    tr : positive float, optional
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
        self.tr = tr
        self.use_afni = use_afni
        self.fractional = fractional

        # Create a name based on the class name if none is provided
        if name is None:
            suffix = "_fractional" if fractional else ""
            name = f"{self.__class__.__name__}{suffix}"
        super().__init__(on="BOLD", name=name)

    def get_valid_inputs(self) -> List[str]:
        """Get valid data types for input.

        Returns
        -------
        list of str
            The list of data types that can be used as input for this marker.

        """
        return ["BOLD"]

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
        return "table"

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
        if self.use_afni is None:
            raise_error(
                "Parameter `use_afni` must be set to True or False in order "
                "to compute this marker. It is currently set to None (default "
                "behaviour). This is intended to be for auto-detection. In "
                "order for that to happen, please call the `validate` method "
                "before calling the `compute` method."
            )

        estimator = AmplitudeLowFrequencyFluctuationEstimator()

        alff, falff = estimator.fit_transform(
            use_afni=self.use_afni,
            input_data=input,
            highpass=self.highpass,
            lowpass=self.lowpass,
            tr=self.tr,
        )
        post_data = falff if self.fractional else alff

        post_input = {
            "data": post_data,
            "path": None,
        }

        out = self._postprocess(post_input)

        return out

    @abstractmethod
    def _postprocess(self, input: Dict) -> Dict:
        """Postprocess the output of the estimator.

        Parameters
        ----------
        input : dict
            The output of the estimator. It must have the following
        """
        raise_error(
            "_postprocess must be implemented", klass=NotImplementedError
        )
