"""Provide abstract base class for markers."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Any, Optional, Union

from ..pipeline import PipelineStepMixin, UpdateMetaMixin
from ..typing import StorageLike
from ..utils import logger, raise_error


__all__ = ["BaseMarker"]


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
    AttributeError
        If the marker does not have `_MARKER_INOUT_MAPPINGS` attribute.
    ValueError
        If required input data type(s) is(are) not found.

    """

    def __init__(
        self,
        on: Optional[Union[list[str], str]] = None,
        name: Optional[str] = None,
    ) -> None:
        # Check for missing mapping attribute
        if not hasattr(self, "_MARKER_INOUT_MAPPINGS"):
            raise_error(
                msg=("Missing `_MARKER_INOUT_MAPPINGS` for the marker"),
                klass=AttributeError,
            )
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
        if not any(x in input for x in self._on):
            raise_error(
                "Input does not have the required data."
                f"\t Input: {input}"
                f"\t Required (any of): {self._on}"
            )
        return [x for x in self._on if x in input]

    def get_valid_inputs(self) -> list[str]:
        """Get valid data types for input.

        Returns
        -------
        list of str
            The list of data types that can be used as input for this marker.

        """
        return list(self._MARKER_INOUT_MAPPINGS.keys())

    def get_output_type(self, input_type: str, output_feature: str) -> str:
        """Get output type.

        Parameters
        ----------
        input_type : str
            The data type input to the marker.
        output_feature : str
            The feature output of the marker.

        Returns
        -------
        str
            The storage type output of the marker.

        """
        return self._MARKER_INOUT_MAPPINGS[input_type][output_feature]

    @abstractmethod
    def compute(self, input: dict, extra_input: Optional[dict] = None) -> dict:
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
        feature: str,
        out: dict[str, Any],
        storage: StorageLike,
    ) -> None:
        """Store.

        Parameters
        ----------
        type_ : str
            The data type to store.
        feature : str
            The feature to store.
        out : dict
            The computed result as a dictionary to store.
        storage : storage-like
            The storage class, for example, SQLiteFeatureStorage.

        """
        output_type_ = self.get_output_type(type_, feature)
        logger.debug(f"Storing {output_type_} in {storage}")
        storage.store(kind=output_type_, **out)

    def _fit_transform(
        self,
        input: dict[str, dict],
        storage: Optional[StorageLike] = None,
    ) -> dict:
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
                # Initialize empty dictionary if no storage object is provided
                if storage is None:
                    out[type_] = {}
                # Store individual features
                for feature_name, feature_data in t_out.items():
                    # Make deep copy of the feature data for manipulation
                    feature_data_copy = deepcopy(feature_data)
                    # Make deep copy of metadata and add to feature data
                    feature_data_copy["meta"] = deepcopy(t_meta)
                    # Update metadata for the feature,
                    # feature data is not manipulated, only meta
                    self.update_meta(feature_data_copy, "marker")
                    # Update marker feature's metadata name
                    feature_data_copy["meta"]["marker"][
                        "name"
                    ] += f"_{feature_name}"

                    if storage is not None:
                        logger.info(f"Storing in {storage}")
                        self.store(
                            type_=type_,
                            feature=feature_name,
                            out=feature_data_copy,
                            storage=storage,
                        )
                    else:
                        logger.info(
                            "No storage specified, returning dictionary"
                        )
                        out[type_][feature_name] = feature_data_copy

        return out
