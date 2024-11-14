"""Provide mixin class for pipeline step."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import sys


if sys.version_info < (3, 11):  # pragma: no cover
    from importlib_metadata import packages_distributions
else:
    from importlib.metadata import packages_distributions


from importlib.util import find_spec
from itertools import chain
from typing import Any

from ..utils import raise_error
from .utils import check_ext_dependencies


__all__ = ["PipelineStepMixin"]


class PipelineStepMixin:
    """Mixin class for a pipeline step."""

    def validate_input(self, input: list[str]) -> list[str]:
        """Validate the input to the pipeline step.

        Parameters
        ----------
        input : list of str
            The input to the pipeline step. The list must contain the
            available Junifer Data dictionary keys.

        Returns
        -------
        list of str
            The actual elements of the input that will be processed by this
            pipeline step.

        Raises
        ------
        ValueError
            If the input does not have the required data.

        """
        raise_error(
            msg="Concrete classes need to implement validate_input().",
            klass=NotImplementedError,
        )  # pragma: no cover

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
        )  # pragma: no cover

    def _fit_transform(
        self,
        input: dict[str, dict],
    ) -> dict[str, dict]:
        """Fit and transform.

        Parameters
        ----------
        input : dict
            The Junifer Data object.

        Returns
        -------
        dict
            The processed output of the pipeline step.

        """
        raise_error(
            msg="Concrete classes need to implement _fit_transform().",
            klass=NotImplementedError,
        )  # pragma: no cover

    def validate(self, input: list[str]) -> list[str]:
        """Validate the the pipeline step.

        Parameters
        ----------
        input : list of str
            The input to the pipeline step.

        Returns
        -------
        list of str
            The output of the pipeline step.

        """

        def _check_dependencies(obj) -> None:
            """Check obj._DEPENDENCIES.

            Parameters
            ----------
            obj : object
                Object to check _DEPENDENCIES of.

            Raises
            ------
            ImportError
                If the pipeline step object is missing dependencies required
                for its working.

            """
            # Check if _DEPENDENCIES attribute is found;
            # (markers and preprocessors will have them but not datareaders
            # as of now)
            dependencies_not_found = []
            if hasattr(obj, "_DEPENDENCIES"):
                # Check if dependencies are importable
                for dependency in obj._DEPENDENCIES:
                    # First perform an easy check
                    if find_spec(dependency) is None:
                        # Then check mapped names
                        if dependency not in list(
                            chain.from_iterable(
                                packages_distributions().values()
                            )
                        ):
                            dependencies_not_found.append(dependency)
            # Raise error if any dependency is not found
            if dependencies_not_found:
                raise_error(
                    msg=(
                        f"{dependencies_not_found} are not installed but are "
                        f"required for using {obj.__class__.__name__}."
                    ),
                    klass=ImportError,
                )

        def _check_ext_dependencies(obj) -> None:
            """Check obj._EXT_DEPENDENCIES.

            Parameters
            ----------
            obj : object
                Object to check _EXT_DEPENDENCIES of.

            """
            # Check if _EXT_DEPENDENCIES attribute is found;
            # (some markers and preprocessors might have them)
            if hasattr(obj, "_EXT_DEPENDENCIES"):
                for dependency in obj._EXT_DEPENDENCIES:
                    check_ext_dependencies(**dependency)

        def _check_conditional_dependencies(obj) -> None:
            """Check obj._CONDITIONAL_DEPENDENCIES.

            Parameters
            ----------
            obj : object
                Object to check _CONDITIONAL_DEPENDENCIES of.

            Raises
            ------
            AttributeError
                If the pipeline step object does not have `using` as a
                constructor parameter.

            """
            # Check if _CONDITIONAL_DEPENDENCIES attribute is found;
            # (some markers and preprocessors might have them)
            if hasattr(obj, "_CONDITIONAL_DEPENDENCIES"):
                if not hasattr(obj, "using"):
                    raise_error(
                        msg=(
                            f"The pipeline step: {obj.__class__.__name__} has "
                            "`_CONDITIONAL_DEPENDENCIES` but does not have "
                            "`using` as a constructor parameter"
                        ),
                        klass=AttributeError,
                    )
                else:
                    for dependency in obj._CONDITIONAL_DEPENDENCIES:
                        if dependency["using"] == obj.using:
                            depends_on = dependency["depends_on"]
                            # Conditional to make `using="auto"` work
                            if not isinstance(depends_on, list):
                                depends_on = [depends_on]
                            for entry in depends_on:
                                # Check dependencies
                                _check_dependencies(entry)
                                # Check external dependencies
                                _check_ext_dependencies(entry)

        # Check dependencies
        _check_dependencies(self)
        # Check external dependencies
        _check_ext_dependencies(self)
        # Check conditional dependencies
        _check_conditional_dependencies(self)
        # Validate input
        fit_input = self.validate_input(input=input)
        # Validate output type
        # Nested output type for marker
        if hasattr(self, "_MARKER_INOUT_MAPPINGS"):
            outputs = list(
                {
                    val
                    for t_input in fit_input
                    for val in self._MARKER_INOUT_MAPPINGS[t_input].values()
                }
            )
        else:
            outputs = [self.get_output_type(t_input) for t_input in fit_input]
        return outputs

    def fit_transform(
        self, input: dict[str, dict], **kwargs: Any
    ) -> dict[str, dict]:
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
