"""Provide abstract base class for markers."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from ..pipeline import PipelineStepMixin, UpdateMetaMixin
from ..utils import logger, raise_error


if TYPE_CHECKING:
    from junifer.storage import BaseFeatureStorage


class BaseMarker(ABC, PipelineStepMixin, UpdateMetaMixin):
    """Abstract base class for all markers.

    For every interface that is required, one needs to provide a concrete
    implementation of this abstract class.

    Parameters
    ----------
    on : str or list of str or None, optional
        The data type to apply the marker on. If None,
        will work on all available data types (default None).
    name : str, optional
        The name of the marker. If None, will use the class name as the
        name of the marker (default None).

    Raises
    ------
    ValueError
        If required input data type(s) is(are) not found.

    """

    def __init__(
        self,
        on: Optional[Union[List[str], str]] = None,
        name: Optional[str] = None,
    ) -> None:
        # Use all data types if not provided
        if on is None:
            on = self.get_valid_inputs()
        # Convert data types to list
        if not isinstance(on, list):
            on = [on]
        # Set default name if not provided
        self.name = self.__class__.__name__ if name is None else name
        # Check if required inputs are found
        if any(x not in self.get_valid_inputs() for x in on):
            wrong_on = [x for x in on if x not in self.get_valid_inputs()]
            raise_error(f"{self.name} cannot be computed on {wrong_on}")
        self._on = on

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
        if not any(x in input for x in self._on):
            raise_error(
                "Input does not have the required data."
                f"\t Input: {input}"
                f"\t Required (any of): {self._on}"
            )
        return [x for x in self._on if x in input]

    @abstractmethod
    def get_valid_inputs(self) -> List[str]:
        """Get valid data types for input.

        Returns
        -------
        list of str
            The list of data types that can be used as input for this marker.

        """
        raise_error(
            msg="Concrete classes need to implement get_valid_inputs().",
            klass=NotImplementedError,
        )

    @abstractmethod
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

    @abstractmethod
    def compute(self, input: Dict, extra_input: Optional[Dict] = None) -> Dict:
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
            with this as a parameter.

        """
        raise_error(
            msg="Concrete classes need to implement compute().",
            klass=NotImplementedError,
        )

    def store(
        self,
        type_: str,
        out: Dict[str, Any],
        storage: "BaseFeatureStorage",
    ) -> None:
        """Store.

        Parameters
        ----------
        type_ : str
            The data type to store.
        out : dict
            The computed result as a dictionary to store.
        storage : storage-like
            The storage class, for example, SQLiteFeatureStorage.

        """
        output_type_ = self.get_output_type(type_)
        logger.debug(f"Storing {output_type_} in {storage}")
        storage.store(kind=output_type_, **out)

    def _fit_transform(
        self,
        input: Dict[str, Dict],
        storage: Optional["BaseFeatureStorage"] = None,
    ) -> Dict:
        """Fit and transform.

        Parameters
        ----------
        input : dict
            The Junifer Data object.
        storage : storage-like, optional
            The storage class, for example, SQLiteFeatureStorage.

        Returns
        -------
        dict
            The processed output as a dictionary. If `storage` is provided,
            empty dictionary is returned.

        """
        out = {}
        for type_ in self._on:
            if type_ in input.keys():
                logger.info(f"Computing {type_}")
                # Get data dict for data type
                t_input = input[type_]
                # Pass the other data types as extra input, removing
                # the current type
                extra_input = input.copy()
                extra_input.pop(type_)
                logger.debug(
                    f"Extra data type for feature extraction: "
                    f"{extra_input.keys()}"
                )
                # Copy metadata
                t_meta = t_input["meta"].copy()
                t_meta["type"] = type_
                # Compute marker
                t_out = self.compute(input=t_input, extra_input=extra_input)
                t_out["meta"] = t_meta
                # Update metadata for step
                self.update_meta(t_out, "marker")
                # Check storage
                if storage is not None:
                    logger.info(f"Storing in {storage}")
                    self.store(type_=type_, out=t_out, storage=storage)
                else:
                    logger.info("No storage specified, returning dictionary")
                    out[type_] = t_out

        return out
