"""Provide mixin class for pipeline step."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Dict, List

from ..utils import raise_error


class PipelineStepMixin:
    """Mixin class for pipeline."""

    def get_meta(self) -> Dict:
        """Get metadata.

        Returns
        -------
        dict
            The metadata as a dictionary.

        """
        t_meta = {}
        t_meta["class"] = self.__class__.__name__
        for k, v in vars(self).items():
            if not k.startswith("_"):
                t_meta[k] = v
        return t_meta

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

    def get_output_kind(self, input: List[str]) -> List[str]:
        """Get the kind of the pipeline step.

        Parameters
        ----------
        input : list of str
            The input to the pipeline step. The list must contain the
            available Junifer Data dictionary keys.

        Returns
        -------
        list of str
            The updated list of available Junifer Data dictionary keys after
            the pipeline step.

        """
        raise_error(
            msg="Concrete classes need to implement get_output_kind().",
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
        return self.get_output_kind(input=input)

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
