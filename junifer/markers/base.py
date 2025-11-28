"""Provide abstract base class for markers."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Any, ClassVar, Optional

from pydantic import BaseModel, ConfigDict

from ..datagrabber import DataType
from ..pipeline import PipelineStepMixin, UpdateMetaMixin
from ..storage import StorageType
from ..typing import MarkerInOutMappings, StorageLike
from ..utils import logger, raise_error


__all__ = ["BaseMarker"]


class BaseMarker(BaseModel, ABC, PipelineStepMixin, UpdateMetaMixin):
    """Abstract base class for marker.

    For every marker, one needs to provide a concrete
    implementation of this abstract class.

    Parameters
    ----------
    on : :enum:`.DataType` or list of variants or None, optional
        The data type(s) to apply the marker on.
        If None, will work on all available data types.
        Check :enum:`.DataType` for valid values (default None).
    name : str or None, optional
        The name of the marker.
        If None, will use the class name (default None).

    Attributes
    ----------
    valid_inputs

    Raises
    ------
    AttributeError
        If the marker does not have ``_MARKER_INOUT_MAPPINGS`` attribute.
    ValueError
        If required input data type(s) is(are) not found.

    """

    _MARKER_INOUT_MAPPINGS: ClassVar[MarkerInOutMappings]

    model_config = ConfigDict(use_enum_values=True)

    on: Optional[list[DataType]] = None
    name: Optional[str] = None

    def model_post_init(self, context: Any):  # noqa: D102
        # Check for missing mapping attribute
        if not hasattr(self, "_MARKER_INOUT_MAPPINGS"):
            raise_error(
                msg=("Missing `_MARKER_INOUT_MAPPINGS` for the marker"),
                klass=AttributeError,
            )
        # Use all data types if not provided
        if self.on is None:
            self.on = self.valid_inputs
        else:
            # Convert to correct data type
            self.on = [DataType(t) for t in self.on]
            # Check if required input data types are provided
            if any(x not in self.valid_inputs for x in self.on):
                wrong_on = [
                    x.value for x in self.on if x not in self.valid_inputs
                ]
                raise_error(
                    f"{self.__class__.__name__} cannot be computed on "
                    f"{wrong_on}"
                )
        # Run extra validation for markers and fail early if needed
        self.validate_marker_params()
        # Set default name if not provided
        self.name = self.__class__.__name__ if self.name is None else self.name

    @property
    def valid_inputs(self) -> list[DataType]:
        """Valid data types to operate on.

        Returns
        -------
        list of :enum:`.DataType`
            The list of data types that can be used as input for this marker.

        """
        return [DataType(x) for x in self._MARKER_INOUT_MAPPINGS.keys()]

    def validate_marker_params(self) -> None:
        """Run extra logical validation for marker.

        Subclasses can override to provide validation.
        """
        pass

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
        if not any(x in input for x in self.on):
            raise_error(
                "Input does not have the required data.\n"
                f"\t Input: {input}\n"
                f"\t Required (any of): {[t.value for t in self.on]}"
            )
        return [x.value for x in self.on if x in input]

    def storage_type(
        self, input_type: DataType, output_feature: str
    ) -> StorageType:
        """Get :enum:`.StorageType` for a feature.

        Parameters
        ----------
        input_type : :enum:`.DataType`
            The data type input to the marker.
        output_feature : str
            The feature output of the marker.

        Returns
        -------
        :enum:`.StorageType`
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
        data_type: DataType,
        feature: str,
        output: dict[str, Any],
        storage: StorageLike,
    ) -> None:
        """Store.

        Parameters
        ----------
        data_type : :enum:`.DataType`
            The data type to store.
        feature : str
            The feature to store.
        output : dict
            The computed result as a dictionary to store.
        storage : storage-like
            The storage class, for example, SQLiteFeatureStorage.

        """
        s_type = self.storage_type(data_type, feature)
        logger.debug(f"Storing {s_type} in {storage}")
        storage.store(kind=s_type, **output)

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
            The processed output as a dictionary. If ``storage`` is provided,
            empty dictionary is returned.

        """
        out = {}
        for t in self.on:
            if t in input.keys():
                logger.info(f"Computing {t}")
                # Get data dict for data type
                t_input = input[t]
                # Pass the other data types as extra input, removing
                # the current type
                extra_input = input.copy()
                extra_input.pop(t)
                logger.debug(
                    f"Extra data type for feature extraction: "
                    f"{extra_input.keys()}"
                )
                # Copy metadata
                t_meta = t_input["meta"].copy()
                t_meta["type"] = t.value
                # Compute marker
                t_out = self.compute(input=t_input, extra_input=extra_input)
                # Initialize empty dictionary if no storage object is provided
                if storage is None:
                    out[t] = {}
                # Store individual features
                for f_name, f_data in t_out.items():
                    # Make deep copy of the feature data for manipulation
                    f_data_copy = deepcopy(f_data)
                    # Make deep copy of metadata and add to feature data
                    f_data_copy["meta"] = deepcopy(t_meta)
                    # Update metadata for the feature,
                    # feature data is not manipulated, only meta
                    self.update_meta(f_data_copy, "marker")
                    # Update marker feature's metadata name
                    f_data_copy["meta"]["marker"]["name"] += f"_{f_name}"

                    if storage is not None:
                        logger.info(f"Storing in {storage}")
                        self.store(
                            data_type=t,
                            feature=f_name,
                            output=f_data_copy,
                            storage=storage,
                        )
                    else:
                        logger.info(
                            "No storage specified, returning dictionary"
                        )
                        out[t][f_name] = f_data_copy

        return out
