"""Provide abstract base class for preprocessor."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union

from ..pipeline import PipelineStepMixin, UpdateMetaMixin
from ..utils import logger, raise_error


class BasePreprocessor(ABC, PipelineStepMixin, UpdateMetaMixin):
    """Provide abstract base class for all preprocessors.

    Parameters
    ----------
    on : str or list of str, optional
        The kind of data to apply the preprocessor to. If None,
        will work on all available data (default None).
    required_data_types : str or list of str, optional
        The kind of data types needed for computation. If None,
        will be equal to ``on`` (default None).

    Raises
    ------
    ValueError
        If required input data type(s) is(are) not found.

    """

    def __init__(
        self,
        on: Optional[Union[List[str], str]] = None,
        required_data_types: Optional[Union[List[str], str]] = None,
    ) -> None:
        """Initialize the class."""
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
            self._required_data_types = required_data_types

    def validate_input(self, input: List[str]) -> List[str]:
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

    @abstractmethod
    def get_valid_inputs(self) -> List[str]:
        """Get valid data types for input.

        Returns
        -------
        list of str
            The list of data types that can be used as input for this
            preprocessor.

        """
        raise_error(
            msg="Concrete classes need to implement get_valid_inputs().",
            klass=NotImplementedError,
        )

    @abstractmethod
    def get_output_type(self, input: List[str]) -> List[str]:
        """Get output type.

        Parameters
        ----------
        input : list of str
            The input to the preprocessor. The list must contain the
            available Junifer Data dictionary keys.

        Returns
        -------
        list of str
            The updated list of available Junifer Data object keys after
            the pipeline step.

        """
        raise_error(
            msg="Concrete classes need to implement get_output_type().",
            klass=NotImplementedError,
        )

    @abstractmethod
    def preprocess(
        self,
        input: Dict[str, Any],
        extra_input: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """Preprocess.

        Parameters
        ----------
        input : dict
            A single input from the Junifer Data object to preprocess.
        extra_input : dict, optional
            The other fields in the Junifer Data object. Useful for accessing
            other data kind that needs to be used in the computation. For
            example, the confound removers can make use of the
            confounds if available (default None).

        Returns
        -------
        str
            The key to store the output in the Junifer Data object.
        dict
            The computed result as dictionary. This will be stored in the
            Junifer Data object under the key ``data`` of the data type.

        """
        raise_error(
            msg="Concrete classes need to implement preprocess().",
            klass=NotImplementedError,
        )

    def _fit_transform(
        self,
        input: Dict[str, Dict],
    ) -> Dict:
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
        out = input
        for type_ in self._on:
            if type_ in input.keys():
                logger.info(f"Preprocessing {type_}")
                t_input = input[type_]

                # Pass the other data types as extra input, removing
                # the current type
                extra_input = input
                extra_input.pop(type_)
                logger.debug(
                    f"Extra input for preprocess: {extra_input.keys()}"
                )
                key, t_out = self.preprocess(
                    input=t_input, extra_input=extra_input
                )

                # Add the output to the Junifer Data object
                logger.debug(f"Adding {key} to output")
                out[key] = t_out

                # In case we are creating a new type, re-add the original input
                if key != type_:
                    logger.debug("Adding original input back to output")
                    out[type_] = t_input

                self.update_meta(out[key], "preprocess")
        return out
