"""Provide mixin class for pipeline step."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Dict, List

from ..utils import raise_error


class PipelineStepMixin:
    """Mixin class for pipeline."""

    def validate_input(self, input: List[str]) -> None:
        """Validate the input to the pipeline step.

        Parameters
        ----------
        input : list of str
            The input to the pipeline step. The list must contain the
            available Junifer Data dictionary keys.

        Raises
        ------
        ValueError
            If the input does not have the required data.

        """
        raise_error(
            msg="Concrete classes need to implement validate_input().",
            klass=NotImplementedError,
        )

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
        raise_error(
            msg="Concrete classes need to implement get_output_type().",
            klass=NotImplementedError,
        )

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
            If the input does not have the required data.

        """
        self.validate_input(input=input)
        outputs = [self.get_output_type(t_input) for t_input in input]
        return outputs

    def fit_transform(self, input: Dict[str, Dict]) -> Dict[str, Dict]:
        """Fit and transform.

        Parameters
        ----------
        input : list of str
            The input to the pipeline step. The list must contain the
            available Junifer Data dictionary keys.

        """
        raise_error(
            msg="Concrete classes need to implement fit_transform().",
            klass=NotImplementedError,
        )
