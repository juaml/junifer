"""Provide mixin class for pipeline step."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

try:
    from importlib.metadata import packages_distributions
except ImportError:  # pragma: no cover
    from importlib_metadata import packages_distributions

from importlib.util import find_spec
from itertools import chain
from typing import Any, Dict, List

from ..utils import raise_error
from .utils import check_ext_dependencies


class PipelineStepMixin:
    """Mixin class for a pipeline step."""

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

    def _fit_transform(
        self, input: Dict[str, Dict], **kwargs: Any
    ) -> Dict[str, Dict]:
        """Fit and transform.

        Parameters
        ----------
        input : dict
            The Junifer Data object.
        **kwargs : dict
            Extra keyword arguments.

        Returns
        -------
        dict
            The processed output of the pipeline step.

        """
        raise_error(
            msg="Concrete classes need to implement _fit_transform().",
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
                # First perform an easy check
                if find_spec(dependency) is None:
                    # Then check mapped names
                    if dependency not in list(
                        chain.from_iterable(packages_distributions().values())
                    ):
                        dependencies_not_found.append(dependency)
        # Raise error if any dependency is not found
        if dependencies_not_found:
            raise_error(
                msg=f"{dependencies_not_found} are not installed but are "
                "required for using {self.name}.",
                klass=ImportError,
            )
        # Check if _EXT_DEPENDENCIES attribute is found;
        # (some markers might have them like ReHo-family)
        if hasattr(self, "_EXT_DEPENDENCIES"):
            for dependency in self._EXT_DEPENDENCIES:  # type: ignore
                out = check_ext_dependencies(**dependency)
                if getattr(self, f"use_{dependency['name']}", None) is None:
                    # Set attribute for using external tools
                    setattr(self, f"use_{dependency['name']}", out)

        self.validate_input(input=input)
        outputs = [self.get_output_type(t_input) for t_input in input]
        return outputs

    def fit_transform(
        self, input: Dict[str, Dict], **kwargs: Any
    ) -> Dict[str, Dict]:
        """Fit and transform.

        Parameters
        ----------
        input : dict
            The Junifer Data object.
        **kwargs : dict
            Extra keyword arguments passed to the concrete class'
            _fit_transform().

        Returns
        -------
        dict
            The processed output of the pipeline step.

        """
        self.validate(input=list(input.keys()))
        return self._fit_transform(input=input, **kwargs)
