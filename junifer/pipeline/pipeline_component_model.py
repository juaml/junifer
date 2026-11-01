"""Provide the base model of the pipeline components."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator

from .update_meta_mixin import UpdateMetaMixin


__all__ = ["PipelineComponentModel"]


class PipelineComponentModel(BaseModel, UpdateMetaMixin):
    """Base model of the pipeline components.

    The behaviour shared by the pydantic models of the pipeline components
    (e.g., the DataGrabbers, DataReaders, preprocessors and markers):

    * The validation of their parameters: unknown parameters are not allowed
      (``extra="forbid"``) and the enumerations are stored as their values
      (``use_enum_values=True``). Subclasses can change it with their own
      ``model_config``.
    * Their metadata (:meth:`.UpdateMetaMixin.update_meta`), with the names of
      the parameters given when creating them (``_fields_set``), to generate
      the YAML that computes a feature again (:func:`.generate_yaml`).

    """

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    # The names of the parameters given when creating the object, e.g., the
    # ones in the YAML. They are stored in the metadata (``update_meta``) to
    # generate the YAML that computes a feature again (``generate_yaml``),
    # with only these parameters (the others keep their default values). None
    # if the object was not created from a dictionary of parameters.
    _fields_set: set[str] | None = None

    @model_validator(mode="wrap")
    @classmethod
    def _store_fields_set(cls, data: Any, handler: Callable) -> Any:
        """Store the names of the parameters given, before validating them.

        A wrap model validator runs around the whole validation, so the
        parameters changed or set by the validation (e.g., in
        ``model_post_init``, even if a subclass overrides it) are not
        included.

        Parameters
        ----------
        data : Any
            The data to validate (the parameters, if a dictionary).
        handler : callable
            The validation of the data.

        Returns
        -------
        Any
            The validated object.

        """
        keys = set(data) if isinstance(data, dict) else None
        obj = handler(data)
        if keys is not None:
            obj._fields_set = keys
        return obj
