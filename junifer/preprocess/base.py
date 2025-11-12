"""Provide abstract base class for preprocessor."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any, ClassVar, Optional, Union

from ..pipeline import PipelineStepMixin, UpdateMetaMixin
from ..utils import logger, raise_error


__all__ = ["BasePreprocessor"]


class BasePreprocessor(ABC, PipelineStepMixin, UpdateMetaMixin):
    """Abstract base class for preprocessor.

    For every preprocessor, one needs to provide a concrete
    implementation of this abstract class.

    Parameters
    ----------
    on : str or list of str or None, optional
        The data type(s) to apply the preprocessor on. If None,
        will work on all available data types (default None).
    required_data_types : str or list of str, optional
        The data types needed for computation. If None,
        will be equal to ``on`` (default None).

    Raises
    ------
    AttributeError
        If the preprocessor does not have `_VALID_DATA_TYPES` attribute.
    ValueError
        If required input data type(s) is(are) not found.

    """

    _VALID_DATA_TYPES: ClassVar[Sequence[str]]

    def __init__(
        self,
        on: Optional[Union[list[str], str]] = None,
        required_data_types: Optional[Union[list[str], str]] = None,
    ) -> None:
        """Initialize the class."""
        # Check for missing data types attributes
        if not hasattr(self, "_VALID_DATA_TYPES"):
            raise_error(
                msg="Missing `_VALID_DATA_TYPES` for the preprocessor",
                klass=AttributeError,
            )
        # Use all data types if not provided
        if on is None:
            on = self.get_valid_inputs()
        # Convert data types to list
        if not isinstance(on, list):
            on = [on]
        # Check if required inputs are found
        if any(x not in self.get_valid_inputs() for x in on):
            name = self.__class__.__name__
            wrong_on = [x for x in on if x not in self.get_valid_inputs()]
            raise_error(f"{name} cannot be computed on {wrong_on}")
        self._on = on
        # Set required data types for validation
        if required_data_types is None:
            self._required_data_types = on
        else:
            # Convert data types to list
            if not isinstance(required_data_types, list):
                required_data_types = [required_data_types]
            self._required_data_types = required_data_types

    def validate_input(self, input: list[str]) -> list[str]:
        """Validate input.

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
        if any(x not in input for x in self._required_data_types):
            raise_error(
                "Input does not have the required data."
                f"\t Input: {input}"
                f"\t Required (all of): {self._required_data_types}"
            )
        return [x for x in self._on if x in input]

    def get_valid_inputs(self) -> list[str]:
        """Get valid data types for input.

        Returns
        -------
        list of str
            The list of data types that can be used as input for this
            preprocessor.

        """
        return list(self._VALID_DATA_TYPES)

    @abstractmethod
    def preprocess(
        self,
        input: dict[str, Any],
        extra_input: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Preprocess.

        Parameters
        ----------
        input : dict
            A single input from the Junifer Data object to preprocess.
        extra_input : dict, optional
            The other fields in the Junifer Data object. Useful for accessing
            other data type that needs to be used in the computation. For
            example, the confound removers can make use of the
            confounds if available (default None).

        Returns
        -------
        dict
            The computed result as dictionary.

        """
        raise_error(
            msg="Concrete classes need to implement preprocess().",
            klass=NotImplementedError,
        )

    def _fit_transform(
        self,
        input: dict[str, dict],
    ) -> dict:
        """Fit and transform.

        Parameters
        ----------
        input : dict
            The Junifer Data object.

        Returns
        -------
        dict
            The processed output as a dictionary.

        """
        # Copy input to not modify the original
        out = input.copy()
        # For each data type, run preprocessing
        for type_ in self._on:
            # Check if data type is available
            if type_ in input.keys():
                logger.info(f"Preprocessing {type_}")
                # Get data dict for data type
                t_input = input[type_]
                # Pass the other data types as extra input, removing
                # the current type
                extra_input = input.copy()
                extra_input.pop(type_)
                logger.debug(
                    f"Extra data type for preprocess: {extra_input.keys()}"
                )
                # Preprocess data
                t_out = self.preprocess(input=t_input, extra_input=extra_input)
                # Set output to the Junifer Data object
                logger.debug(f"Adding {type_} to output")
                out[type_] = t_out
                # Update metadata for step
                self.update_meta(out[type_], "preprocess")
        return out
