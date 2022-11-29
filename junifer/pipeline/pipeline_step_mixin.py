"""Provide mixin class for pipeline step."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from importlib.util import find_spec
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
            If the pipeline step object is missing dependencies required for
            its working or if the input does not have the required data.

        """
        # Check if _DEPENDENCIES attribute is found;
        # (markers and preprocessors will have them but not datareaders
        # as of now)
        dependencies_not_found = []
        if hasattr(self, "_DEPENDENCIES"):
            # Check if dependencies are importable
            for dependency in self._DEPENDENCIES:  # type: ignore
                if find_spec(dependency) is None:
                    dependencies_not_found.append(dependency)
        # Raise error if any dependency is not found
        if dependencies_not_found:
            raise_error(
                msg=f"{dependencies_not_found} are not installed but are "
                "required for using {self.name}.",
                klass=ImportError,
            )

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
