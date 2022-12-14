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

    Parameters
    ----------
    on : str or list of str
        The kind of data to apply the marker to. By default, will work on all
        available data.
    name : str, optional
        The name of the marker. By default, it will use the class name as the
        name of the marker (default None).

    """

    def __init__(
        self,
        on: Optional[Union[List[str], str]] = None,
        name: Optional[str] = None,
    ) -> None:
        if on is None:
            on = self.get_valid_inputs()
        if not isinstance(on, list):
            on = [on]
        self.name = self.__class__.__name__ if name is None else name

        if any(x not in self.get_valid_inputs() for x in on):
            wrong_on = [x for x in on if x not in self.get_valid_inputs()]
            raise ValueError(f"{self.name} cannot be computed on {wrong_on}")
        self._on = on

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

    def validate_input(self, input: List[str]) -> None:
        """Validate input.

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
        if not any(x in input for x in self._on):
            raise_error(
                "Input does not have the required data."
                f"\t Input: {input}"
                f"\t Required (any of): {self._on}"
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
                t_input = input[type_]
                extra_input = input.copy()
                extra_input.pop(type_)
                t_meta = t_input["meta"].copy()
                t_meta["type"] = type_

                t_out = self.compute(input=t_input, extra_input=extra_input)
                t_out["meta"] = t_meta

                self.update_meta(t_out, "marker")

                if storage is not None:
                    logger.info(f"Storing in {storage}")
                    self.store(type_=type_, out=t_out, storage=storage)
                else:
                    logger.info("No storage specified, returning dictionary")
                    out[type_] = t_out

        return out
